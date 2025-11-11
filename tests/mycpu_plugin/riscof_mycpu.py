import os
import shutil
import subprocess
import logging

import riscof.utils as utils
from riscof.pluginTemplate import pluginTemplate

logger = logging.getLogger()

class mycpu(pluginTemplate):
    __model__ = "mycpu"
    __version__ = "0.1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get('config')

        if config is None:
            print("Please provide configuration")
            raise SystemExit(1)

        self.num_jobs = str(config['jobs'] if 'jobs' in config else 1)
        self.pluginpath = os.path.abspath(config['pluginpath'])
        self.isa_spec = os.path.abspath(config['ispec'])
        self.platform_spec = os.path.abspath(config['pspec'])

        # Path to MyCPU project (can be 1-single-cycle, 2-mmio-trap, or 3-pipeline)
        self.mycpu_project = os.path.abspath(config['PATH'])

        if 'target_run' in config and config['target_run'] == '0':
            self.target_run = False
        else:
            self.target_run = True

    def initialise(self, suite, work_dir, archtest_env):
        self.work_dir = work_dir
        self.suite_dir = suite

        # Try to find RISC-V GCC (support multiple naming conventions)
        riscv_prefix = None
        for prefix in ['riscv32-unknown-elf', 'riscv-none-elf', 'riscv64-unknown-elf']:
            if shutil.which(f'{prefix}-gcc'):
                riscv_prefix = prefix
                break

        if not riscv_prefix:
            raise RuntimeError("RISC-V GCC not found. Tried: riscv32-unknown-elf-gcc, riscv-none-elf-gcc")

        # Compile command for RISC-V tests
        self.compile_cmd = (f'{riscv_prefix}-gcc -march={{0}} '
            '-static -mcmodel=medany -fvisibility=hidden -nostdlib -nostartfiles '
            f'-T {self.pluginpath}/env/link.ld '
            f'-I {self.pluginpath}/env/ '
            f'-I {archtest_env} {{1}} -o {{2}} {{3}}')
        self.riscv_objcopy = f'{riscv_prefix}-objcopy'

    def build(self, isa_yaml, platform_yaml):
        ispec = utils.load_yaml(isa_yaml)['hart0']
        self.xlen = ('64' if 64 in ispec['supported_xlen'] else '32')
        self.isa = 'rv' + self.xlen

        # Standard single-letter extensions
        if "I" in ispec["ISA"]:
            self.isa += 'i'
        if "M" in ispec["ISA"]:
            self.isa += 'm'
        if "A" in ispec["ISA"]:
            self.isa += 'a'
        if "F" in ispec["ISA"]:
            self.isa += 'f'
        if "D" in ispec["ISA"]:
            self.isa += 'd'
        if "C" in ispec["ISA"]:
            self.isa += 'c'

        # Z-extensions (Zicsr, Zifencei, etc.)
        if "Zicsr" in ispec["ISA"]:
            self.isa += '_zicsr'
        if "Zifencei" in ispec["ISA"]:
            self.isa += '_zifencei'

        self.compile_cmd = self.compile_cmd + f' -mabi=' + ('lp64 ' if 64 in ispec['supported_xlen'] else 'ilp32 ') + f'-DXLEN={self.xlen} '
        logger.debug(f'Compile command template: {self.compile_cmd}')

    def runTests(self, testList):
        total_tests = len(testList)
        test_num = 0
        for testname in testList:
            test_num += 1
            testentry = testList[testname]
            test = testentry['test_path']
            test_dir = testentry['work_dir']

            logger.info(f'Running test {test_num}/{total_tests}: {testname}')

            elf = os.path.join(test_dir, 'dut.elf')
            sig_file = os.path.join(test_dir, 'DUT-mycpu.signature')

            # Compile test to ELF
            compile_cmd = self.compile_cmd.format(testentry['isa'].lower(), test, elf, '')

            logger.debug('Compiling test: ' + compile_cmd)
            utils.shellCommand(compile_cmd).run(cwd=test_dir)

            # Verify ELF was created
            if not os.path.exists(elf):
                logger.error(f'ELF compilation failed: {elf} not created')
                continue

            # Convert ELF to asmbin format for MyCPU
            asmbin = os.path.join(test_dir, 'test.asmbin')
            objcopy_cmd = f'{self.riscv_objcopy} -O binary {elf} {asmbin}'
            logger.debug('Converting to asmbin: ' + objcopy_cmd)
            utils.shellCommand(objcopy_cmd).run(cwd=test_dir)

            # Run ChiselTest to execute CPU simulation
            if self.target_run:
                # Copy asmbin file to MyCPU resources
                resource_dir = os.path.join(self.mycpu_project, 'src/main/resources')
                os.makedirs(resource_dir, exist_ok=True)
                shutil.copy(asmbin, os.path.join(resource_dir, 'test.asmbin'))

                # Generate test file
                test_scala = self._generate_test_scala(testname, elf, sig_file, asmbin)
                dest_path = os.path.join(self.mycpu_project, 'src/test/scala/riscv/compliance/ComplianceTest.scala')
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                with open(dest_path, 'w') as f:
                    f.write(test_scala)

                # Run sbt test in the MyCPU project with timeout and proper error handling
                # Map directory name to SBT project name for multi-project build
                project_dir_name = os.path.basename(self.mycpu_project)
                project_map = {
                    '1-single-cycle': 'singleCycle',
                    '2-mmio-trap': 'mmioTrap',
                    '3-pipeline': 'pipeline'
                }
                sbt_project_name = project_map.get(project_dir_name, 'singleCycle')

                # Run from parent directory with project selection (multi-project SBT structure)
                parent_dir = os.path.dirname(self.mycpu_project)
                log_file = os.path.join(test_dir, 'sbt_output.log')
                # Disable SBT server completely via java system property to prevent boot lock conflicts
                # Combined with isolated sbt.global.base for complete test isolation
                # Create unique SBT base to avoid rt.jar file conflicts between parallel tests
                # Increased timeout to 300s for complex tests like misalign1-jalr-01.S
                sbt_global_base = os.path.join(test_dir, '.sbt-global')
                # Use SBT_OPTS to pass -Dsbt.server.forcestart=false (disable server mode entirely)
                execute = f'cd {parent_dir} && SBT_OPTS="-Dsbt.server.forcestart=false" timeout 300 sbt -Dsbt.global.base={sbt_global_base} --batch "project {sbt_project_name}" "testOnly riscv.compliance.ComplianceTest" > {log_file} 2>&1'
                logger.debug(f'Running test: {execute}')

                try:
                    utils.shellCommand(execute).run()

                    if os.path.exists(sig_file):
                        logger.info(f'Signature generated: {sig_file}')
                    else:
                        logger.warning(f'Signature file not created: {sig_file}')
                        if os.path.exists(log_file):
                            with open(log_file, 'r') as f:
                                error_log = f.read()
                                if 'error' in error_log.lower() or 'failed' in error_log.lower():
                                    logger.error(f'Test execution errors detected. See {log_file} for details.')
                        # Create empty signature to allow RISCOF to continue
                        with open(sig_file, 'w') as f:
                            for i in range(256):
                                f.write('00000000\n')
                except Exception as e:
                    logger.error(f'Test execution failed: {e}')
                    if os.path.exists(log_file):
                        logger.error(f'See {log_file} for detailed error output')
                    # Create empty signature to allow RISCOF to continue
                    with open(sig_file, 'w') as f:
                        for i in range(256):
                            f.write('00000000\n')

        return

    def _generate_test_scala(self, testname, elfFile, sigFile, asmbinFile):
        """Generate Scala test file for this compliance test"""
        return f'''// Auto-generated compliance test
package riscv.compliance

import riscv.TestAnnotations

class ComplianceTest extends ComplianceTestBase {{
  behavior.of("MyCPU Compliance")

  it should "pass test {testname}" in {{
    runComplianceTest(
      "test.asmbin",
      "{elfFile}",
      "{sigFile}",
      TestAnnotations.annos
    )
  }}
}}
'''
