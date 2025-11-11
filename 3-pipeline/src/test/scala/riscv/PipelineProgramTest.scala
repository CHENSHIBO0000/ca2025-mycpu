// SPDX-License-Identifier: MIT
// MyCPU is freely redistributable under the MIT License. See the file
// "LICENSE" for information on usage and redistribution of this file.

package riscv

import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec
import riscv.core.CSRRegister

class PipelineProgramTest extends AnyFlatSpec with ChiselScalatestTester {
  private val mcauseAcceptable: Set[BigInt] =
    Set(BigInt("80000007", 16), BigInt("8000000B", 16))

  private def runProgram(exe: String, cfg: PipelineConfig)(body: TestTopModule => Unit): Unit = {
    test(new TestTopModule(exe, cfg.implementation))
      .withAnnotations(TestAnnotations.annos) { c =>
        c.io.csr_debug_read_address.poke(0.U)
        c.io.interrupt_flag.poke(0.U)
        body(c)
      }
  }

  for (cfg <- PipelineConfigs.All) {
    behavior.of(cfg.name)

    it should "calculate recursively fibonacci(10)" in {
      runProgram("fibonacci.asmbin", cfg) { c =>
        for (i <- 1 to 50) {
          c.clock.step(1000)
          c.io.mem_debug_read_address.poke((i * 4).U)
        }
        c.io.mem_debug_read_address.poke(4.U)
        c.clock.step()
        c.io.mem_debug_read_data.expect(55.U)
      }
    }

    it should "quicksort 10 numbers" in {
      runProgram("quicksort.asmbin", cfg) { c =>
        for (i <- 1 to 50) {
          c.clock.step(1000)
          c.io.mem_debug_read_address.poke((i * 4).U)
        }
        for (i <- 1 to 10) {
          c.io.mem_debug_read_address.poke((4 * i).U)
          c.clock.step()
          c.io.mem_debug_read_data.expect((i - 1).U)
        }
      }
    }

    it should "store and load single byte" in {
      runProgram("sb.asmbin", cfg) { c =>
        c.clock.step(1000)
        c.io.regs_debug_read_address.poke(5.U)
        c.io.regs_debug_read_data.expect(0xdeadbeefL.U)
        c.io.regs_debug_read_address.poke(6.U)
        c.io.regs_debug_read_data.expect(0xef.U)
        c.io.regs_debug_read_address.poke(1.U)
        c.io.regs_debug_read_data.expect(0x15ef.U)
      }
    }

    it should "solve data and control hazards" in {
      runProgram("hazard.asmbin", cfg) { c =>
        c.clock.step(1000)
        c.io.regs_debug_read_address.poke(1.U)
        c.io.regs_debug_read_data.expect(cfg.hazardX1.U)
        c.io.mem_debug_read_address.poke(4.U)
        c.clock.step()
        c.io.mem_debug_read_data.expect(1.U)
        c.io.mem_debug_read_address.poke(8.U)
        c.clock.step()
        c.io.mem_debug_read_data.expect(3.U)
      }
    }

    it should "handle machine-mode traps" in {
      runProgram("irqtrap.asmbin", cfg) { c =>
        c.clock.setTimeout(0)
        for (i <- 1 to 1000) {
          c.clock.step()
          c.io.mem_debug_read_address.poke((i * 4).U)
        }
        c.io.mem_debug_read_address.poke(4.U)
        c.clock.step()
        c.io.mem_debug_read_data.expect(0xdeadbeefL.U)

        c.io.interrupt_flag.poke(1.U)
        c.clock.step(5)
        c.io.interrupt_flag.poke(0.U)

        for (i <- 1 to 1000) {
          c.clock.step()
          c.io.mem_debug_read_address.poke((i * 4).U)
        }
        c.io.csr_debug_read_address.poke(CSRRegister.MSTATUS)
        c.clock.step()
        c.io.csr_debug_read_data.expect(0x1888.U)
        c.io.csr_debug_read_address.poke(CSRRegister.MCAUSE)
        c.clock.step()
        val cause = c.io.csr_debug_read_data.peek().litValue
        assert(mcauseAcceptable.contains(cause), f"unexpected mcause 0x${cause}%x")
        c.io.mem_debug_read_address.poke(0x4.U)
        c.clock.step()
        c.io.mem_debug_read_data.expect(0x2022L.U)
      }
    }
  }
}
