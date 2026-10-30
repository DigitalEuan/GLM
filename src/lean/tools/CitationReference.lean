/-
  The elaborator's citation graph of the GLM development.

  Not part of the library (it lives outside `RequestProject/`, so `lake build`
  never compiles it).  `glm_universal.reasoning.citation_reference` prepends an
  `import` line for every module of `RequestProject/GLM` and runs it with
  `lake env lean`.  For every constant declared in a `RequestProject.GLM`
  module it prints one line:

      <name> TAB <module> TAB <constant> <constant> ...

  where the constants are those of the same development that occur in the
  constant's type or value (`ConstantInfo.getUsedConstantsAsSet`).  Private
  names are printed as the name the user wrote.
-/
open Lean in
#eval show CoreM Unit from do
  let env ← getEnv
  let mods := env.header.moduleNames
  let moduleOf (n : Name) : Option Name :=
    (env.getModuleIdxFor? n).map fun i => mods[i.toNat]!
  let inGLM (n : Name) : Bool :=
    match moduleOf n with
    | some m => (`RequestProject.GLM).isPrefixOf m
    | none => false
  let userName (n : Name) : String := ((privateToUserName? n).getD n).toString
  for (n, ci) in env.constants.map₁.toList do
    if inGLM n then
      let used := ci.getUsedConstantsAsSet.toList.filter fun c => inGLM c && c != n
      let m := (moduleOf n).getD Name.anonymous
      IO.println s!"{userName n}\t{m}\t{" ".intercalate (used.map userName)}"
