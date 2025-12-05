// SPDX-License-Identifier: MIT
// MyCPU is freely redistributable under the MIT License. See the file
// "LICENSE" for information on usage and redistribution of this file.

package riscv.core

import chisel3._
import riscv.Parameters

class PipelineRegister(width: Int = Parameters.DataBits, defaultValue: UInt = 0.U) extends Module {
  val io = IO(new Bundle {
    val stall = Input(Bool())
    val flush = Input(Bool())
    val in    = Input(UInt(width.W))
    val out   = Output(UInt(width.W))
  })
  val myreg = RegInit(UInt(width.W), defaultValue)
  val out   = RegInit(UInt(width.W), defaultValue)
  when(io.flush) {
    out   := defaultValue
    myreg := defaultValue
  }
    .elsewhen(io.stall) {
      out := myreg
    }
    .otherwise {
      myreg := io.in
      out   := io.in
    }
  io.out := out 
}
