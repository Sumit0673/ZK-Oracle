// This is a stub lib.rs that will be populated by risc0-build.
// It exports the guest ELF binary and image ID constants:
//   - ORACLE_GUEST_ELF: the compiled guest program
//   - ORACLE_GUEST_ID: the unique identifier for the guest program
//
// These are auto-generated at build time from the guest code.
include!(concat!(env!("OUT_DIR"), "/methods.rs"));
