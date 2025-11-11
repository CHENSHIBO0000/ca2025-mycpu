// SPDX-License-Identifier: MIT
// MyCPU is freely redistributable under the MIT License. See the file
// "LICENSE" for information on usage and redistribution of this file.

package riscv.core.threestage

import chisel3._
import chisel3.util.MuxLookup
import riscv.Parameters

object InterruptStatus {
  val None   = 0x0.U(8.W)
  val Timer0 = 0x1.U(8.W)
  val Ret    = 0xff.U(8.W)
}

class CSRDirectAccessBundle extends Bundle {
  val mstatus = Input(UInt(Parameters.DataWidth))
  val mepc    = Input(UInt(Parameters.DataWidth))
  val mcause  = Input(UInt(Parameters.DataWidth))
  val mtvec   = Input(UInt(Parameters.DataWidth))

  val mstatus_write_data = Output(UInt(Parameters.DataWidth))
  val mepc_write_data    = Output(UInt(Parameters.DataWidth))
  val mcause_write_data  = Output(UInt(Parameters.DataWidth))

  val direct_write_enable = Output(Bool())
}

// Core Local Interrupt Controller
class CLINT extends Module {
  val io = IO(new Bundle {
    val interrupt_flag = Input(UInt(Parameters.InterruptFlagWidth))

    val instruction_ex         = Input(UInt(Parameters.InstructionWidth))
    val instruction_address_if = Input(UInt(Parameters.AddrWidth))
    val instruction_address_id = Input(UInt(Parameters.AddrWidth))

    val jump_flag    = Input(Bool())
    val jump_address = Input(UInt(Parameters.AddrWidth))

    val ex_interrupt_handler_address = Output(UInt(Parameters.AddrWidth))
    val ex_interrupt_assert          = Output(Bool())

    val csr_bundle = new CSRDirectAccessBundle
  })
  val interrupt_enable = io.csr_bundle.mstatus(3)
  val jumpping         = RegNext(io.jump_flag || io.ex_interrupt_assert)
  val instruction_address = Mux(
    io.jump_flag,
    io.jump_address,
    Mux(jumpping, io.instruction_address_if, io.instruction_address_id)
  )
  val mstatus_disable_interrupt = io.csr_bundle.mstatus(31, 4) ## 0.U(1.W) ## io.csr_bundle.mstatus(2, 0)
  val mstatus_recover_interrupt =
    io.csr_bundle.mstatus(31, 4) ## io.csr_bundle.mstatus(7) ## io.csr_bundle.mstatus(2, 0)
  val exception        = io.instruction_ex === InstructionsEnv.ecall || io.instruction_ex === InstructionsEnv.ebreak
  val interrupt        = io.interrupt_flag =/= InterruptStatus.None && interrupt_enable
  val mret             = io.instruction_ex === InstructionsRet.mret
  val interrupt_assert = exception || interrupt || mret

  io.csr_bundle.mstatus_write_data := Mux(mret, mstatus_recover_interrupt, mstatus_disable_interrupt)
  io.csr_bundle.mepc_write_data    := instruction_address
  io.csr_bundle.mcause_write_data := Mux(
    exception,
    MuxLookup(
      io.instruction_ex,
      10.U
    )(
      IndexedSeq(
        InstructionsEnv.ecall  -> 11.U,
        InstructionsEnv.ebreak -> 3.U,
      )
    ),
    Mux(io.interrupt_flag(0), 0x80000007L.U, 0x8000000bL.U)
  )
  io.csr_bundle.direct_write_enable := interrupt_assert
  io.ex_interrupt_assert            := interrupt_assert
  io.ex_interrupt_handler_address   := Mux(mret, io.csr_bundle.mepc, io.csr_bundle.mtvec)
}
