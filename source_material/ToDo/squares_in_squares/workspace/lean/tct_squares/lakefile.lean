import Lake
open Lake DSL

package tct_squares where
  require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.8.0"

lean_lib TCT where
  globs := #[.andSubmodules `TCT]

@[default_target]
lean_exe check where
  root := `Main
