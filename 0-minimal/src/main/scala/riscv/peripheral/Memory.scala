// SPDX-License-Identifier: MIT
// MyCPU is freely redistributable under the MIT License. See the file
// "LICENSE" for information on usage and redistribution of this file.

package riscv.peripheral

import chisel3._
import chisel3.util._
import riscv.Parameters

class RAMBundle extends Bundle {
  val address      = Input(UInt(Parameters.AddrWidth))
  val write_data   = Input(UInt(Parameters.DataWidth))
  val write_enable = Input(Bool())
  val write_strobe = Input(Vec(Parameters.WordSize, Bool()))
  val read_data    = Output(UInt(Parameters.DataWidth))
}

// Minimal Memory: unified instruction and data memory
class Memory(capacity: Int) extends Module {
  val io = IO(new Bundle {
    val bundle = new RAMBundle

    val instruction         = Output(UInt(Parameters.DataWidth))
    val instruction_address = Input(UInt(Parameters.AddrWidth))

    val debug_read_address = Input(UInt(Parameters.AddrWidth))
    val debug_read_data    = Output(UInt(Parameters.DataWidth))
  })

  val mem = SyncReadMem(capacity, Vec(Parameters.WordSize, UInt(Parameters.ByteWidth)))

  val max_word_address = (capacity - 1).U

  // Memory writes: address truncated to word index (>>2), misaligned accesses write to aligned word
  // Out-of-bounds writes are silently dropped (no error signaling)
  when(io.bundle.write_enable) {
    val write_data_vec = Wire(Vec(Parameters.WordSize, UInt(Parameters.ByteWidth)))
    for (i <- 0 until Parameters.WordSize) {
      write_data_vec(i) := io.bundle.write_data((i + 1) * Parameters.ByteBits - 1, i * Parameters.ByteBits)
    }
    val write_word_addr = (io.bundle.address >> 2.U).asUInt
    when(write_word_addr <= max_word_address) {
      mem.write(write_word_addr, write_data_vec, io.bundle.write_strobe)
    }
  }

  // Memory reads: address truncated to word index (>>2), misaligned accesses read from aligned word
  // Out-of-bounds reads return data from address 0 (no error signaling)
  val read_word_addr = Mux(
    (io.bundle.address >> 2.U).asUInt <= max_word_address,
    (io.bundle.address >> 2.U).asUInt,
    0.U
  )
  val debug_word_addr = Mux(
    (io.debug_read_address >> 2.U).asUInt <= max_word_address,
    (io.debug_read_address >> 2.U).asUInt,
    0.U
  )
  val inst_word_addr = Mux(
    (io.instruction_address >> 2.U).asUInt <= max_word_address,
    (io.instruction_address >> 2.U).asUInt,
    0.U
  )

  io.bundle.read_data := mem.read(read_word_addr, true.B).asUInt
  io.debug_read_data  := mem.read(debug_word_addr, true.B).asUInt
  io.instruction      := mem.read(inst_word_addr, true.B).asUInt
}
