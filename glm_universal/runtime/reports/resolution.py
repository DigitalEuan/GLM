"""``glm_universal.runtime.reports.resolution``
-- the subjects that measure what a layer can and cannot tell apart.

Reports about resolution: what is conflated, and where.

Information loss at the layer boundaries, the same audit at register
scale, the resolution ceiling a name reaches, and the measure word read
against a comparison class together with the denotation residue.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...reasoning import denotation_view as dvw
from ...reasoning import escalation as esc
from ...reasoning import information_loss as il
from ...reasoning import measure_view as mvw
from ...reasoning import name_coordinate as nco

from ..payload import noise_payload
from ..parser import Query
from ..solution import Solution, Step, q


class ResolutionReports:
    """The subjects that measure what a layer can and cannot tell apart.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_information_loss(self, query: Query) -> Solution:
        """Wires il.information_loss_report — loss at the layer boundaries.

        Each layer of the stack is true within its own reach and hands off to
        the next.  This report measures where a reach ends: what each layer
        cannot tell apart, which pairs the layer above it splits, and whether
        addition can be computed from what the layer sees.
        """
        report = il.information_loss_report()
        by_name = {layer["name"]: layer for layer in report["layers"]}
        edges = {(b["lower"], b["higher"]): b for b in report["boundaries"]}
        names = tuple(layer["name"] for layer in report["layers"])
        pairs = tuple((b["lower"], b["higher"])
                      for b in report["boundaries"])
        raw = report["non_cumulative"]

        resolutions = ", ".join(
            f"{n} {by_name[n]['resolution']}/{report['carrier_count']}"
            for n in names)
        descends = ", ".join(
            n for n in names if by_name[n]["addition_descends"]) or "none"
        lost = ", ".join(
            f"{lo}->{hi} {edges[(lo, hi)]['lost_count']}" for lo, hi in pairs)
        holes = [f"{lo}->{hi}" for lo, hi in pairs
                 if not edges[(lo, hi)]["refines"]]

        steps = [
            Step("resolution",
                 f"On {report['carrier_count']} carriers chosen to exercise "
                 f"every handoff, each layer's own measure decides which of "
                 f"them it can tell apart.  What it cannot tell apart is what "
                 f"it loses.",
                 f"resolved: {resolutions}"),
            Step("boundary",
                 f"The boundary between two layers is the set of pairs the "
                 f"lower one conflates and the higher one splits.  That set "
                 f"is exactly the information recovered by escalating -- and "
                 f"exactly the information the lower layer was never wrong "
                 f"to ignore, within its own reach.",
                 f"lost pairs: {lost}"),
            Step("reach of the law",
                 f"Coordinatewise addition descends to a layer only when the "
                 f"layer's view determines the view of the sum.  Where a "
                 f"witness exists -- indistinguishable inputs with "
                 f"distinguishable sums -- the law is true one level up and "
                 f"untrue here.",
                 f"addition descends at: {descends}"),
            Step("refinement audit",
                 f"A stack is a refinement chain when every layer sees at "
                 f"least as much as the one below.  Where it is not, "
                 f"escalation itself loses information.",
                 f"chain intact: {report['refinement_chain_intact']}"
                 + (f"; holes at {', '.join(holes)}" if holes else "")),
            Step("what cumulativity buys",
                 f"The chain is intact because each layer keeps what the "
                 f"one below it saw and adds to it.  The reading that only "
                 f"takes the seven SI7 exponents is kept beside the stack "
                 f"to show the difference: it conflates carriers the "
                 f"substrate already separates, so a stack built on it "
                 f"would lose information by escalating.",
                 f"{raw['layer']}: refines substrate "
                 f"{raw['refines_substrate']}, "
                 f"{raw['violation_count']} violating pair(s); "
                 f"{raw['cumulative_layer']}: "
                 f"{raw['cumulative_refines_substrate']}"),
        ]

        expected = {"carrier_count": str(report["carrier_count"])}
        for name in names:
            layer = by_name[name]
            expected[f"resolution_{name}"] = str(layer["resolution"])
            expected[f"loss_{name}"] = str(layer["loss_count"])
            expected[f"addition_descends_{name}"] = str(
                layer["addition_descends"])
        for lower, higher in pairs:
            edge = edges[(lower, higher)]
            key = f"{lower}_to_{higher}"
            expected[f"lost_count_{key}"] = str(edge["lost_count"])
            expected[f"refines_{key}"] = str(edge["refines"])
        expected["refinement_chain_intact"] = str(
            report["refinement_chain_intact"])
        expected["non_cumulative_refines_substrate"] = str(
            raw["refines_substrate"])
        expected["non_cumulative_violations"] = str(raw["violation_count"])
        expected["cumulative_refines_substrate"] = str(
            raw["cumulative_refines_substrate"])

        return Solution(
            query=query, kind="report",
            answer=f"report information loss: resolved {resolutions}; "
                   f"lost {lost}; addition descends at {descends}; "
                   f"refinement chain intact "
                   f"{report['refinement_chain_intact']}; "
                   f"non-cumulative SI7 reading refines substrate "
                   f"{raw['refines_substrate']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_information_loss", "args": {}},
            payload={"report": report})

    def _report_escalation(self, query: Query) -> Solution:
        """Wires esc.escalation_report -- the layer stack on every register.

        ``report information loss`` runs the layer audit on seven carriers
        chosen to exhibit one boundary each.  This subject runs the same audit
        on the machine's own data: one carrier per named object of all six
        shipped registers.  The audit is keyed rather than pairwise -- each
        layer's measure is zero exactly when a cheap reading of the two
        carriers agrees -- and the sixth step re-derives that identification
        from the layers themselves on a fixed sample, so the fast path is
        checked rather than trusted.

        The finding the seven-carrier set could not have produced is the
        ceiling: a register is a *naming*, two entries may carry the same
        24 coordinates, and no layer can then tell them apart, because a view
        is a function of the carrier.  ``GLM.Info.entryResolution_le_distinct``
        is that as a theorem, and the measurement says how far below the
        ceiling the registers sit.
        """
        report = esc.escalation_report()
        sizes = report["register_sizes"]
        layers = {l["name"]: l for l in report["layers"]}
        boundaries = report["boundaries"]
        ceiling = report["ceiling"]
        agreement = report["key_agreement"]
        raw = report["non_cumulative"]
        top = layers["universal"]
        witness = layers["substrate"]["congruence_witness"]

        steps = [
            Step("the carrier set is the registers, not a fixture",
                 f"One carrier per named object of every register the "
                 f"package ships, in register order and with nothing "
                 f"sampled: "
                 f"{', '.join(f'{k} {sizes[k]}' for k in report['registers'])}"
                 f".  The seven carriers of "
                 f"`report information loss` were each chosen to exhibit a "
                 f"boundary; these were chosen by nobody.",
                 f"{report['carrier_count']} carriers from "
                 f"{len(report['registers'])} registers"),
            Step("the audit is keyed, so it is linear",
                 f"Every layer's measure is a sum of non-negative exact "
                 f"terms and is zero exactly when a small reading of the two "
                 f"carriers agrees: parity bits at the substrate, the SI7 "
                 f"exponents beside them at the integer layer, the exact "
                 f"carrier at the three above.  Grouping by that reading "
                 f"replaces the quadratic scan, and the quartic congruence "
                 f"search, with one pass.",
                 f"keys: " + "; ".join(
                     f"{name} -- {layers[name]['key']}"
                     for name in ("substrate", "integer", "rational"))),
            Step("what each layer resolves, at scale",
                 f"Resolution rises with the layer and stops rising at the "
                 f"rational one, whose view is the carrier itself.  "
                 f"`GLM.Info.entryResolution_mono` proves the order cannot "
                 f"invert however the registers grow.",
                 "; ".join(f"{l['name']} {l['resolution']}/"
                           f"{report['carrier_count']} "
                           f"(loses {l['loss_count']}, largest class "
                           f"{l['largest_class']})"
                           for l in report["layers"])),
            Step("what each boundary gains, and that none loses",
                 f"A step is a refinement exactly when no pair it conflates "
                 f"was split below it.  Every step of the shipped stack "
                 f"passes here, on a thousand carriers rather than seven, "
                 f"and the two steps above the rational layer gain nothing "
                 f"because there is nothing left to gain.",
                 "; ".join(f"{b['lower']} -> {b['higher']}: gained "
                           f"{b['gained']}, violations {b['violations']}"
                           for b in boundaries)
                 + f"; chain intact {report['refinement_chain_intact']}"),
            Step("the ceiling: what escalation can never resolve",
                 f"A register names carriers, and the naming is not "
                 f"injective: {ceiling['unreachable']} of "
                 f"{ceiling['entries']} entries share a carrier with another "
                 f"entry, in {ceiling['collision_classes']} classes, every "
                 f"one of them inside a single register.  No layer sees "
                 f"anything but the carrier, so no layer separates them -- "
                 f"the largest class is {ceiling['largest_class_size']} "
                 f"dimensionless {ceiling['largest_class_register']} "
                 f"quantities ({', '.join(ceiling['largest_class_examples'][:3])}"
                 f", ...).  What is missing is not resolution but a "
                 f"coordinate for the name.",
                 f"{ceiling['distinct_carriers']} distinct carriers of "
                 f"{ceiling['entries']} entries; unreachable "
                 f"{ceiling['unreachable']}; cross-register collisions "
                 f"{ceiling['cross_register']}; by register "
                 + "; ".join(f"{r['register']} {r['unreachable']}/"
                             f"{r['entries']}"
                             for r in report["by_register"])),
            Step("where addition still descends",
                 f"Addition descends to the three layers whose view is the "
                 f"carrier, and to neither of the two below: the readings "
                 f"take an integer part first, so a half unit and the vacuum "
                 f"agree while their doubles do not.  The witness here is "
                 f"drawn from the registers themselves, and the same "
                 f"argument is `GLM.Info.substrate_addition_not_congruent`.",
                 f"descends: " + ", ".join(
                     l["name"] for l in report["layers"]
                     if l["addition_descends"])
                 + f"; substrate witness "
                 f"{witness['names'][0]} ~ {witness['names'][1]} against "
                 f"{witness['names'][2]}"),
            Step("the keys, re-derived from the layers",
                 f"The fast path is checked rather than trusted: for every "
                 f"pair of a fixed sample and every layer, the layer's own "
                 f"perceive and measure are run and their verdict compared "
                 f"with the key's.  A single disagreement would make this "
                 f"false and name the pair.",
                 f"sample {agreement['sample_size']}, pairs "
                 f"{agreement['pairs_checked']}, agrees "
                 f"{agreement['agrees']}, disagreements "
                 f"{len(agreement['disagreements'])}"),
            Step("the reading the stack rejected, at scale",
                 f"LAYER_INTEGER_RAW reads the seven exponents and discards "
                 f"the substrate's view.  On seven carriers it lost one "
                 f"pair; on the registers it conflates "
                 f"{raw['violations']} pairs the substrate already "
                 f"separates, and resolves {raw['resolution']} where the "
                 f"cumulative reading resolves "
                 f"{raw['cumulative_resolution']}.",
                 f"integer_raw resolves {raw['resolution']}, refines "
                 f"substrate {raw['refines_substrate']}, violations "
                 f"{raw['violations']}, first pair "
                 f"{raw['example_violation_names']}"),
        ]

        expected = {
            "carriers": str(report["carrier_count"]),
            "registers": ",".join(report["registers"]),
            "substrate_resolution": str(layers["substrate"]["resolution"]),
            "integer_resolution": str(layers["integer"]["resolution"]),
            "rational_resolution": str(layers["rational"]["resolution"]),
            "griess_resolution": str(layers["griess"]["resolution"]),
            "universal_resolution": str(top["resolution"]),
            "integer_raw_resolution": str(raw["resolution"]),
            "gained_substrate_integer": str(boundaries[0]["gained"]),
            "gained_integer_rational": str(boundaries[1]["gained"]),
            "gained_rational_griess": str(boundaries[2]["gained"]),
            "gained_griess_universal": str(boundaries[3]["gained"]),
            "chain_intact": str(report["refinement_chain_intact"]),
            "distinct_carriers": str(ceiling["distinct_carriers"]),
            "unreachable": str(ceiling["unreachable"]),
            "collision_classes": str(ceiling["collision_classes"]),
            "cross_register_collisions": str(ceiling["cross_register"]),
            "largest_collision": str(ceiling["largest_class_size"]),
            "unreachable_by_register": ",".join(
                f"{r['register']}:{r['unreachable']}"
                for r in report["by_register"]),
            "addition_descends": ",".join(
                l["name"] for l in report["layers"]
                if l["addition_descends"]),
            "key_agreement": str(agreement["agrees"]),
            "key_pairs_checked": str(agreement["pairs_checked"]),
            "raw_refines_substrate": str(raw["refines_substrate"]),
            "raw_violations": str(raw["violations"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report escalation: the five-layer audit run on "
                   f"{report['carrier_count']} register carriers rather than "
                   f"seven -- resolution "
                   f"{layers['substrate']['resolution']} -> "
                   f"{layers['integer']['resolution']} -> "
                   f"{layers['rational']['resolution']}, then flat, with "
                   f"every boundary a refinement "
                   f"({report['refinement_chain_intact']}); the ceiling is "
                   f"{ceiling['distinct_carriers']} distinct carriers, so "
                   f"{ceiling['unreachable']} named entries in "
                   f"{ceiling['collision_classes']} classes are beyond every "
                   f"layer, the largest being "
                   f"{ceiling['largest_class_size']} dimensionless "
                   f"quantities; addition descends only where the view is "
                   f"the carrier itself; and the rejected SI7-only reading "
                   f"conflates {raw['violations']} pairs the substrate "
                   f"splits",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_escalation", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_names(self, query: Query) -> Solution:
        """Wires nco.name_report -- the resolution ceiling, attacked.

        ``report escalation`` measured a ceiling and named its cause: a
        layer's view is a function of the carrier, so entries that share a
        carrier are beyond every layer, and what is missing is a coordinate
        for the name rather than a finer layer.  This subject supplies the
        coordinate and reports what it buys, which is the separate question.

        Three things are reported and the middle one is the point.  An exact
        injective code lifts the ceiling completely, which
        ``GLM.Info.namedResolution_of_injective`` says is forced rather than
        discovered -- it fixes the coordinate as an *address*, in the sense of
        directive D3, and adds nothing to any quantity's meaning.  A code
        reduced to ``b`` bits brings the ceiling back gradually, and the sweep
        is where the measurement lives; ``GLM.Info.card_le_of_codeInjOn`` puts
        a floor under it, since a class of ``n`` entries at one carrier needs
        at least ``n`` codes.  And the controls decide whether it is the name
        doing the work: the register label is a coordinate computed from the
        entry too, and it recovers none of the collisions, because every
        collision class lies inside a single register.
        """
        report = nco.name_report()
        before = report["before"]
        exact = report["exact"]
        sweeps = report["sweeps"]
        prime = sweeps["prime_mod"]
        low = sweeps["low_bits"]
        controls = {row["coordinate"]: row for row in report["controls"]}
        sufficient = report["sufficient_bits"]
        low_floor = min(row["unreachable"] for row in low)
        rows_checked = len(prime) + len(low) + len(controls) + 1
        violations = (sum(r["violations"] for r in prime)
                      + sum(r["violations"] for r in low)
                      + sum(r["violations"] for r in controls.values())
                      + exact["violations"])

        def _sweep_text(rows) -> str:
            return ", ".join(f"{r['bits']}b {r['unreachable']}" for r in rows)

        steps = [
            Step("the ceiling, as the layer audit left it",
                 f"{before['unreachable']} of {report['entries']} named "
                 f"entries share a carrier with another entry, in "
                 f"{before['collision_classes']} classes, "
                 f"{before['within_register']} of them inside one register "
                 f"and {before['cross_register']} across registers.  No "
                 f"layer separates them, because every layer's view is a "
                 f"function of the carrier; the largest class is "
                 f"{before['largest_class_size']} "
                 f"{before['largest_class_register']} quantities.",
                 f"{before['distinct_carriers']} distinct carriers of "
                 f"{report['entries']} entries; unreachable "
                 f"{before['unreachable']}"),
            Step("the coordinate is computed from the entry, exactly",
                 f"The name's UTF-8 bytes behind a leading 0x01, read as a "
                 f"big-endian integer.  No float, no hash library, nothing "
                 f"stored beside the entry -- the leading byte puts names of "
                 f"different lengths in disjoint bands, so the map is "
                 f"injective, and the report re-checks that on the shipped "
                 f"corpus rather than assuming it.",
                 f"injective on corpus "
                 f"{report['code_injective_on_corpus']}; "
                 f"{report['distinct_names']} distinct names among "
                 f"{report['entries']} entries"),
            Step("the exact code lifts the ceiling, and that is forced",
                 f"Reading (carrier, code) resolves "
                 f"{exact['distinct']}/{exact['entries']} and recovers all "
                 f"{exact['recovered']}.  It does so from any layer at all: "
                 f"the 24-bit substrate resolves "
                 f"{report['substrate_resolution']} of the entries alone and "
                 f"{report['substrate_resolution_named']} with the name "
                 f"beside it.  `GLM.Info.namedResolution_of_injective` is "
                 f"that as a theorem, which is why the number is worth "
                 f"little on its own: an injective coordinate is an address, "
                 f"not a measurement.",
                 f"exact: distinct {exact['distinct']}, unreachable "
                 f"{exact['unreachable']}, recovered {exact['recovered']}; "
                 f"substrate {report['substrate_resolution']} -> "
                 f"{report['substrate_resolution_named']}"),
            Step("the sweep: how much of the name is needed",
                 f"Reduce the code modulo the largest prime below 2^b and "
                 f"the ceiling returns gradually -- and only inside the "
                 f"collision classes, since entries with different carriers "
                 f"are already apart.  {sufficient['prime_mod']} bits "
                 f"suffice here.  The sweep is not monotone: at 14 bits the "
                 f"modulus is a different prime, so a width that keeps more "
                 f"of the name can collide where a narrower one did not.",
                 f"prime_mod unreachable by width: {_sweep_text(prime)}; "
                 f"sufficient {sufficient['prime_mod']}"),
            Step("the reduction is a choice, and it is measured",
                 f"Keeping the low bits keeps the tail of the name, and the "
                 f"corpus is full of suffix families, so it saturates: it "
                 f"never falls below {low_floor} unreachable however many "
                 f"bits it is given, where the mixing reduction reaches "
                 f"zero at {sufficient['prime_mod']}.  Two coordinates of "
                 f"the same width, the same exactness and the same name -- "
                 f"only the reduction differs.",
                 f"low_bits unreachable by width: {_sweep_text(low)}; "
                 f"sufficient {sufficient['low_bits']}"),
            Step("the floor the pigeonhole forces",
                 f"A class of {before['largest_class_size']} entries at one "
                 f"carrier cannot be separated by fewer than "
                 f"{before['largest_class_size']} codes, so no reduction "
                 f"below {report['forced_bits']} bits can clear the ceiling, "
                 f"whatever it does.  `GLM.Info.card_le_of_codeInjOn` is the "
                 f"argument; the measured sufficient width "
                 f"({sufficient['prime_mod']}) sits above it, as it must.",
                 f"forced {report['forced_bits']} bits <= measured "
                 f"{sufficient['prime_mod']} bits"),
            Step("the controls: coordinates that are not the name",
                 f"Each control is computed from the entry, exactly, by the "
                 f"same rule.  The register label recovers "
                 f"{controls['register']['recovered']} of "
                 f"{before['unreachable']} -- every collision class lies "
                 f"inside one register, so a register coordinate is "
                 f"constant on the classes and cannot split them; "
                 f"`GLM.Info.namedResolution_eq_of_constant_on_classes` "
                 f"proves that a coordinate of that shape recovers exactly "
                 f"nothing.  The first letter and the length are coordinates "
                 f"too, and they recover part, which is what stops the "
                 f"claim being 'one more coordinate helps'.",
                 "; ".join(f"{k} recovered {controls[k]['recovered']}"
                           for k in nco.CONTROLS)),
            Step("the reading is a widening, and the rule is enforced",
                 f"Pairing the carrier with a code can split a class and can "
                 f"never merge two, so the named reading refines the layer's "
                 f"-- `GLM.Info.namedLayer_refines_entryLayer`, and counting "
                 f"merges here would be counting a structural zero.  What is "
                 f"counted instead is the admission rule: every coordinate "
                 f"is evaluated a second time with the entries visited in "
                 f"the opposite order, and a disagreement is a coordinate "
                 f"that read something other than its entry.  Every row of "
                 f"both sweeps and every control is checked.",
                 f"rows checked {rows_checked}, violations {violations}"),
        ]

        expected = {
            "entries": str(report["entries"]),
            "distinct_carriers": str(before["distinct_carriers"]),
            "unreachable_before": str(before["unreachable"]),
            "collision_classes": str(before["collision_classes"]),
            "largest_class": str(before["largest_class_size"]),
            "code_injective": str(report["code_injective_on_corpus"]),
            "distinct_names": str(report["distinct_names"]),
            "exact_distinct": str(exact["distinct"]),
            "exact_unreachable": str(exact["unreachable"]),
            "exact_recovered": str(exact["recovered"]),
            "substrate_resolution": str(report["substrate_resolution"]),
            "substrate_resolution_named":
                str(report["substrate_resolution_named"]),
            "prime_mod_sweep": ",".join(
                f"{r['bits']}:{r['unreachable']}" for r in prime),
            "low_bits_sweep": ",".join(
                f"{r['bits']}:{r['unreachable']}" for r in low),
            "sufficient_bits_prime_mod": str(sufficient["prime_mod"]),
            "sufficient_bits_low_bits": str(sufficient["low_bits"]),
            "low_bits_floor": str(low_floor),
            "forced_bits": str(report["forced_bits"]),
            "control_recovered": ",".join(
                f"{k}:{report['control_recovered'][k]}"
                for k in nco.CONTROLS),
            "rows_checked": str(rows_checked),
            "violations": str(violations),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report names: the resolution ceiling is a coordinate "
                   f"problem, and the coordinate is supplied -- an exact "
                   f"integer read off the entry's own name recovers all "
                   f"{exact['recovered']} of the {before['unreachable']} "
                   f"entries no layer could separate, lifting even the "
                   f"24-bit substrate from {report['substrate_resolution']} "
                   f"to {report['substrate_resolution_named']} of "
                   f"{report['entries']}; that much is forced, so the "
                   f"measurement is the sweep, where "
                   f"{sufficient['prime_mod']} bits suffice against a "
                   f"pigeonhole floor of {report['forced_bits']} and the "
                   f"tail-of-the-name reduction never gets below "
                   f"{low_floor}; and the control settles what is doing the "
                   f"work, since the register label recovers "
                   f"{controls['register']['recovered']} while the first "
                   f"letter recovers {controls['initial']['recovered']} and "
                   f"the length {controls['length']['recovered']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_names", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_measure(self, query: Query) -> Solution:
        """Wires mvw.measure_report -- the relative reading, audited.

        Four things at once, because they are one thing: the comparison-class
        register, the words that do and do not have a measure reading, the
        widening audit (what the relative reading gains, and that it loses
        nothing), and the ``related_to`` residue converted wherever the
        physics register can decide it.
        """
        report = mvw.measure_report()
        denot = dvw.denotation_report()
        denot_register = denot["register"]
        denot_coverage = denot["coverage"]
        denot_pass = denot["second_pass"]
        denot_closure = denot["closure"]
        register = report["register"]
        widening = report["widening"]
        views = {v["name"]: v for v in widening["views"]}
        boundary = widening["boundary"]
        replacement = widening["non_cumulative"]
        witness = report["replacement_witness"]
        witness_replacement = witness["replacement"]
        repair = report["relation_repair"]
        sweep = report["basis_sweep"]
        transport = report["transport"]
        agreement = report["lexicon_agreement"]
        examples = report["examples"]
        refusals = report["refusals"]

        steps = [
            Step("the comparison-class register",
                 f"{register['classes']} classes over "
                 f"{register['quantity_count']} quantities, each an exact "
                 f"bracket in SI base units on a quantity the physics "
                 f"register already holds -- the ten EXT10 exponents are "
                 f"read from there rather than typed again -- beside "
                 f"{register['scales']} measure scales carrying "
                 f"{register['scale_words']} degree words at exact positions "
                 f"on [0, 1].  Where ordinary language and the register name "
                 f"the same quantity differently -- the lexicon's *size* is "
                 f"a volume, its *light* an illuminance, its *heat* an "
                 f"energy and its *weight* a force -- "
                 f"{register['alias_count']} aliases resolve the one to the "
                 f"other; an alias whose target the register does not hold, "
                 f"or which shadows an entry that it does, fails the audit.  "
                 f"Two of them were named by a measure word and the rest by "
                 f"a `related_to` triple that was being declined for the "
                 f"spelling of its endpoint alone.",
                 f"{register['classes']} classes, "
                 f"{register['quantity_count']} quantities "
                 f"{list(register['quantities'])}, "
                 f"{register['scale_words']} scale words, "
                 f"{register['alias_count']} aliases "
                 f"{register['aliases']}, sound "
                 f"{register['aliases_sound']}"),
            Step("the scales agree with the lexicon, and are checked to",
                 f"A degree word that is also a lexicon concept must have "
                 f"that concept's `property_of` quantity, must sit on the "
                 f"side of the midpoint its `positive_negative` primitive "
                 f"says, and an `opposite_of` pair must have positions "
                 f"summing to 1.  {len(agreement['shared_words'])} words are "
                 f"shared and every check passes.  `heavy` is the one word "
                 f"whose polarity is the neutral 1/2 -- the static reading "
                 f"cannot say it is the high pole of mass, and the scale "
                 f"can.",
                 f"shared {agreement['shared_count']}, agrees "
                 f"{agreement['agrees']}, neutral polarity "
                 f"{agreement['polarity_neutral']}, pole pairs "
                 f"{len(agreement['pole_pairs'])}"),
            Step("what a word and a class name together",
                 f"low + position * (high - low), exactly.  The same word "
                 f"against two classes is two measurements, which is the "
                 f"whole content of calling a measure word relative.",
                 "; ".join(f"{e['word']}@{e['comparison_class']} = "
                           f"{q(e['magnitude'])} {e['unit']}"
                           for e in examples)),
            Step("the widening, audited",
                 f"Over the {widening['uses']} uses the registers admit "
                 f"({widening['measured_uses']} measured, "
                 f"{len(widening['unmeasured_words'])} words with no "
                 f"measurement at all), the static reading resolves "
                 f"{views['static']['resolution']} and the widened one "
                 f"{views['measure']['resolution']}.  The step gains "
                 f"{boundary['gained']} pairs and violates refinement "
                 f"{boundary['violations']} times: nothing the lexicon said "
                 f"is given up, which is `GLM.Info."
                 f"measureLayer_refines_staticLayer`.",
                 f"static {views['static']['resolution']}/"
                 f"{widening['uses']}, measure "
                 f"{views['measure']['resolution']}/{widening['uses']}, "
                 f"gained {boundary['gained']}, violations "
                 f"{boundary['violations']}, refines "
                 f"{boundary['refines']}"),
            Step("why it is a widening and not a replacement",
                 f"The rejected design keeps only the measurement.  On the "
                 f"shipped uses it now conflates "
                 f"{replacement['violations']} pairs -- not because it "
                 f"became sound, but because supplying the size and light "
                 f"classes left no word without a measurement for it to "
                 f"fail on.  Re-run over the same uses plus one unmeasured "
                 f"use of each word -- the case that arises the moment a "
                 f"word's quantity is not yet in a register, where large, "
                 f"small and dark stood until this round -- it conflates "
                 f"{witness_replacement['violations']} pairs the lexicon "
                 f"told apart while the widening still conflates "
                 f"{witness['widening']['violations']}.  This is "
                 f"`LAYER_INTEGER_RAW`'s situation exactly, and "
                 f"`GLM.Info.measureReading_not_refines_staticLayer` is the "
                 f"theorem that the failure is a property of the reading "
                 f"rather than of the data.",
                 f"measure_only resolves "
                 f"{views['measure_only']['resolution']}, shipped "
                 f"violations {replacement['violations']}; witness set "
                 f"{witness['uses']} uses, replacement refines "
                 f"{witness_replacement['refines']}, violations "
                 f"{witness_replacement['violations']}, first pair "
                 f"{witness_replacement['example_violation']}"),
            Step("the static reading is the machine's own",
                 f"The audit's static view is checked to be the rational "
                 f"layer of `dimension_layers` on the concept carrier, pair "
                 f"by pair, rather than an idealisation of it.",
                 f"pairs checked "
                 f"{widening['static_agreement']['pairs_checked']}, agrees "
                 f"{widening['static_agreement']['agrees']}"),
            Step("the related_to residue, converted where it can be decided",
                 f"{repair['converted']} of the {repair['related_to']} "
                 f"`related_to` triples are converted by the physics "
                 f"register alone: "
                 f"{repair['by_predicate'].get('same_dimension_as', 0)} "
                 f"same_dimension_as and "
                 f"{repair['by_predicate'].get('differs_by', 0)} differs_by, "
                 f"each with the quantity that carries one dimension to the "
                 f"other.  {repair['residue']} remain, every one with the "
                 f"reason it was declined; nothing is converted on a guess.",
                 f"converted {repair['converted']}/{repair['related_to']}; "
                 + "; ".join(f"{c['subject']} {c['predicate']} {c['object']}"
                             for c in repair["conversions"][:4])),
            Step("the factor basis is a choice, and it is now measured",
                 f"A difference is attributed to one quantity of a fixed "
                 f"basis, and an attribution two members both fit is "
                 f"declined.  Which quantities belong in the basis used to "
                 f"be asserted; it is now swept.  Every one of the "
                 f"{sweep['candidates']} quantities the register holds and "
                 f"the basis did not is offered in turn: "
                 f"{sweep['inert']} change nothing, "
                 f"{sweep['ambiguates']} would make some attribution "
                 f"ambiguous and are refused, and the "
                 f"{sweep['converts']} that strictly convert more occupy "
                 f"only {len(sweep['converting_classes'])} dimensions.  The "
                 f"dimension is what the data decides; the name is not, and "
                 f"the sweep reports the whole class beside each so the "
                 f"spelling stays visible as a choice.",
                 f"basis {sweep['basis_size']} names over "
                 f"{sweep['basis_dimensions']} dimensions (sound "
                 f"{sweep['basis_sound']}), grown by "
                 f"{sweep['grown_by']}; candidates "
                 f"{sweep['candidates']} = {sweep['inert']} inert + "
                 f"{sweep['ambiguates']} ambiguating + "
                 f"{sweep['converts']} converting; "
                 + "; ".join(f"{c['dimension']} gains {c['gain']} "
                             f"({len(c['names'])} names)"
                             for c in sweep["converting_classes"])
                 + f"; converted {sweep['trimmed_counts']['converted']} -> "
                 f"{sweep['shipped_counts']['converted']}"),
            Step("what the residue is made of",
                 f"The refusals are not one kind.  "
                 f"{repair['residue_by_kind'].get('no_single_factor', 0)} "
                 f"of them are a pair of genuine quantities whose "
                 f"difference no single basis factor carries; the other "
                 f"{repair['residue_by_kind'].get('not_a_quantity', 0)} "
                 f"decline because an endpoint is not a quantity at all, "
                 f"and the lexicon's own part of speech says which: "
                 + ", ".join(f"{n} {k}"
                             for k, n in sorted(
                                 repair["residue_by_pos"].items()))
                 + f".  That is a category boundary rather than a data gap: "
                 f"no comparison class makes a verb a magnitude.",
                 "; ".join(f"{k} {v}" for k, v
                           in sorted(repair["residue_by_kind"].items()))
                 + "; by part of speech "
                 + ",".join(f"{k}:{v}" for k, v
                            in sorted(repair["residue_by_pos"].items()))),
            Step("the rest of the residue is decided, not searched",
                 f"'reaches no dimension the register holds' is a fact "
                 f"about a lookup.  It does not say whether there was "
                 f"anything to find, and no amount of searching would "
                 f"settle that.  So the {denot_coverage['needed']} "
                 f"undimensioned endpoints of the residue are decided one "
                 f"name at a time, each with its reason, in "
                 f"`data_objects.denotation`: "
                 + ", ".join(f"{v} {k}" for k, v
                             in denot_register["by_verdict"].items())
                 + f".  Only the first verdict makes a name dimensional and "
                 f"it supplies no coordinate -- *gravity* is the register's "
                 f"`gravitational_field` under an ordinary-language name, "
                 f"exactly as an alias is.  The other five record, on "
                 f"purpose, that the name denotes no magnitude: a carrier "
                 f"bears quantities, a process happens, a polymorphic word "
                 f"takes the dimension of what it is applied to, an "
                 f"ambiguous one ranges over several the register holds and "
                 f"does not choose between them.  The register decides "
                 f"exactly the names the residue asks about: "
                 f"{len(denot_coverage['undecided'])} undecided and "
                 f"{len(denot_coverage['idle'])} idle entries.",
                 f"entries {denot_register['entries']}, needed "
                 f"{denot_coverage['needed']}, complete "
                 f"{denot_coverage['complete']}, audit "
                 f"{denot_register['audit']['sound']}; "
                 + ",".join(f"{k}:{v}" for k, v
                            in denot_register["by_verdict"].items())),
            Step("what the decision changes, measured",
                 f"Re-running the repair with the verdicts in hand: "
                 f"{denot_pass['converted']} of the {denot_pass['residue']} "
                 f"residue triples convert dimensionally -- naming what a "
                 f"word denotes is not a way of manufacturing relations -- "
                 f"{denot_pass['decided']} are repaired to "
                 f"`names_process_of`, the one rule that follows from the "
                 f"verdicts rather than from a reading of each triple, and "
                 f"{denot_pass['declined']} are declined by a reason that "
                 f"now says what the endpoint *is*.  A carrier beside a "
                 f"quantity is deliberately not repaired the same way: a "
                 f"magnet does bear a flux density and a photon does not "
                 f"bear an illuminance, and a rule that is right half the "
                 f"time is a guess.  What is earned is "
                 f"`closure`: {denot_closure['accounted']} of "
                 f"{denot_closure['residue']} accounted for and "
                 f"{len(denot_closure['lookup_failures'])} triples still "
                 f"waiting on an entry.",
                 f"converted {denot_pass['converted']}, decided "
                 f"{denot_pass['decided']}, declined "
                 f"{denot_pass['declined']}, closed "
                 f"{denot_closure['decided']}; "
                 + ",".join(f"{k}:{v}" for k, v
                            in denot_pass["declined_by_kind"].items())),
            Step("the conversions are used, and the control is run",
                 f"A converted relation is only worth having if the machine "
                 f"can transport it.  `related_to` is vague and the analogy "
                 f"layer never transports it; the repaired relations carry "
                 f"the factor in their name, so two pairs differing by "
                 f"different quantities are not treated as the same step.  "
                 f"Of the {transport['cases']} analogies the "
                 f"{transport['triples']} repaired triples license, "
                 f"{transport['answered']} are answered and "
                 f"{transport['refused']} refused.  With the repair "
                 f"suppressed the same analogies answer "
                 f"{transport['control_answered']} -- the one the lexicon "
                 f"could already state for itself.",
                 f"triples {transport['triples']}, distinct relations "
                 f"{transport['predicates']}, transportable "
                 f"{transport['transportable_predicates']}; cases "
                 f"{transport['cases']}, answered {transport['answered']}, "
                 f"control {transport['control_answered']}; "
                 + "; ".join(f"{e['query']} {e['answer']}"
                             for e in transport["examples"][:3])),
            Step("where it refuses, and why that is forced",
                 f"A word the registers cannot reach has no measurement, and "
                 f"`GLM.Info.boundary_empty_of_unmeasured` says the widened "
                 f"view gains nothing between two such uses.  Two of the "
                 f"four refusals below used to be of that kind and are now "
                 f"measured -- `measure large in room_volume` and `measure "
                 f"dark in indoor_lighting` answer -- and what refuses in "
                 f"their place is the honest mismatch: *room* brackets a "
                 f"length and `large` measures a volume.  A word on no "
                 f"scale at all still refuses outright.",
                 "; ".join(f"{r['word']}@{r['class']}: {r['reason']}"
                           for r in refusals)),
        ]

        expected = {
            "classes": str(register["classes"]),
            "quantities": ",".join(register["quantities"]),
            "scale_words": str(register["scale_words"]),
            "lexicon_agreement": str(agreement["agrees"]),
            "shared_words": str(agreement["shared_count"]),
            "scaled_words": str(report["scaled"]),
            "unscaled_words": str(report["unscaled"]),
            "uses": str(widening["uses"]),
            "static_resolution": str(views["static"]["resolution"]),
            "measure_resolution": str(views["measure"]["resolution"]),
            "measure_only_resolution": str(
                views["measure_only"]["resolution"]),
            "gained": str(boundary["gained"]),
            "violations": str(boundary["violations"]),
            "refines": str(boundary["refines"]),
            "replacement_refines": str(replacement["refines"]),
            "replacement_violations": str(replacement["violations"]),
            "witness_uses": str(witness["uses"]),
            "witness_replacement_violations": str(
                witness_replacement["violations"]),
            "witness_widening_violations": str(
                witness["widening"]["violations"]),
            "aliases": ",".join(f"{k}={v}" for k, v
                                in register["aliases"].items()),
            "aliases_sound": str(register["aliases_sound"]),
            "static_agreement": str(
                widening["static_agreement"]["agrees"]),
            "related_to": str(repair["related_to"]),
            "converted": str(repair["converted"]),
            "residue": str(repair["residue"]),
            "same_dimension_as": str(
                repair["by_predicate"].get("same_dimension_as", 0)),
            "differs_by": str(repair["by_predicate"].get("differs_by", 0)),
            "residue_by_kind": ",".join(
                f"{k}:{v}" for k, v in sorted(
                    repair["residue_by_kind"].items())),
            "residue_by_pos": ",".join(
                f"{k}:{v}" for k, v in sorted(
                    repair["residue_by_pos"].items())),
            "denotations": str(denot_register["entries"]),
            "denotation_verdicts": ",".join(
                f"{k}:{v}" for k, v
                in denot_register["by_verdict"].items()),
            "denotation_sound": str(denot_register["audit"]["sound"]),
            "denotation_needed": str(denot_coverage["needed"]),
            "denotation_complete": str(denot_coverage["complete"]),
            "denotation_converted": str(denot_pass["converted"]),
            "denotation_decided": str(denot_pass["decided"]),
            "denotation_declined": str(denot_pass["declined"]),
            "denotation_closed": str(denot_closure["decided"]),
            "basis_size": str(sweep["basis_size"]),
            "basis_dimensions": str(sweep["basis_dimensions"]),
            "basis_sound": str(sweep["basis_sound"]),
            "basis_candidates": str(sweep["candidates"]),
            "basis_inert": str(sweep["inert"]),
            "basis_ambiguates": str(sweep["ambiguates"]),
            "basis_converts": str(sweep["converts"]),
            "basis_converting_dimensions": ",".join(
                str(c["dimension"]) for c in sweep["converting_classes"]),
            "basis_trimmed_converted": str(
                sweep["trimmed_counts"]["converted"]),
            "transport_cases": str(transport["cases"]),
            "transport_answered": str(transport["answered"]),
            "transport_control_answered": str(
                transport["control_answered"]),
            "hot_in_tea": q(examples[0]["magnitude"]),
            "hot_in_stellar_surface": q(examples[1]["magnitude"]),
            "refusal_reasons": ",".join(str(r["reason"]) for r in refusals),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report measure: {register['classes']} comparison "
                   f"classes over {register['quantity_count']} quantities "
                   f"and {register['scale_words']} degree words make "
                   f"{report['scaled']} of the lexicon's "
                   f"{report['scaled'] + report['unscaled']} adjectives "
                   f"measurable -- hot in tea is "
                   f"{q(examples[0]['magnitude'])} K and hot for a stellar "
                   f"surface is {q(examples[1]['magnitude'])} K.  Added as a "
                   f"widening, the relative reading takes the static one "
                   f"from {views['static']['resolution']} to "
                   f"{views['measure']['resolution']} of "
                   f"{widening['uses']} uses, gaining "
                   f"{boundary['gained']} pairs and losing nothing "
                   f"({boundary['violations']} violations), while the "
                   f"replacement reading that drops the concept loses "
                   f"{witness_replacement['violations']} on a witness set "
                   f"that still holds an unmeasured use; and "
                   f"{repair['converted']} of the {repair['related_to']} "
                   f"related_to triples convert to a measured relation, the "
                   f"other {repair['residue']} declining with a reason -- "
                   f"{repair['residue_by_kind'].get('not_a_quantity', 0)} of "
                   f"those because an endpoint is a verb or an abstraction "
                   f"rather than a quantity, every one of them now decided "
                   f"by name in a register of {denot_register['entries']} "
                   f"verdicts that leaves "
                   f"{len(denot_closure['lookup_failures'])} triples waiting "
                   f"on a lookup -- and the conversions carry: "
                   f"{transport['answered']} of the {transport['cases']} "
                   f"analogies they license are transported where the "
                   f"unrepaired control answers "
                   f"{transport['control_answered']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_measure", "args": {}},
            payload={"report": noise_payload(report),
                     "denotation": noise_payload(denot)})
