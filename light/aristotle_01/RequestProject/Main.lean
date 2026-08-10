import Mathlib
import RequestProject.GrayCode
import RequestProject.Golay
import RequestProject.GolayWeights
import RequestProject.Decoder
import RequestProject.Leech
import RequestProject.Shortcut
import RequestProject.Substrate
import RequestProject.FactorMap
import RequestProject.Lightspeed
import RequestProject.SubstrateConstants
import RequestProject.ObserverY

open scoped BigOperators
open scoped Real
open scoped Nat
open scoped Classical
open scoped Pointwise

set_option maxHeartbeats 8000000
set_option maxRecDepth 4000
set_option synthInstance.maxHeartbeats 20000
set_option synthInstance.maxSize 128

set_option relaxedAutoImplicit false
set_option autoImplicit false

set_option pp.fullNames true
set_option pp.structureInstances true
set_option pp.coercions.types true
set_option pp.funBinderTypes true
set_option pp.letVarTypes true
set_option pp.piBinderTypes true

set_option grind.warning false
