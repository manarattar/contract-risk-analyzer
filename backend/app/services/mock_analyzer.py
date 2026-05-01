from app.schemas import (
    ContractAnalysis, ClauseAnalysis, ClauseCategory, AffectedParty,
    ContradictionFinding, ContractQualitySummary, MissingClause, MissingClauseRelevance, RiskLevel,
)

MOCK_ANALYSIS = ContractAnalysis(
    document_summary=(
        "This Software Development Services Agreement contains several significant risk clauses "
        "that heavily favour the Vendor. The liability cap is set too low, the IP assignment is "
        "overbroad, and the termination penalty is disproportionate. Revision is recommended before signing."
    ),
    analysis_perspective="Balanced / both parties",
    overall_risk_score=68,
    overall_risk_level=RiskLevel.MEDIUM,
    quality_summary=ContractQualitySummary(
        overall_legal_structure="Adequate",
        commercial_balance="One-sided",
        drafting_clarity="Adequate",
        enforceability_confidence="Medium",
        negotiation_readiness="Needs revision",
    ),
    final_recommendation="Reasonable with revisions",
    main_risks=[
        "Liability cap of 30 days' fees is far below commercial standard, leaving Client exposed",
        "IP assignment transfers Vendor's pre-existing tools to Client — likely to be disputed",
        "25% termination fee on remaining contract value is disproportionate",
    ],
    minor_improvements=[
        "Payment terms should allow withholding on disputed deliverables",
        "Non-solicitation scope and geography are broader than necessary",
    ],
    best_practice_clauses=[
        "Confidentiality — mutual, clear 3-year survival period",
    ],
    missing_clauses=[
        MissingClause(
            clause_type="Data Protection",
            relevance=MissingClauseRelevance.RECOMMENDED,
            reason="Software development services typically involve access to Client systems or data.",
        ),
        MissingClause(
            clause_type="Dispute Resolution",
            relevance=MissingClauseRelevance.RECOMMENDED,
            reason="Without a defined process, disputes default to litigation.",
        ),
        MissingClause(
            clause_type="Indemnity",
            relevance=MissingClauseRelevance.RECOMMENDED,
            reason="Indemnity for IP infringement and third-party claims is standard in service agreements.",
        ),
    ],
    contradictions=[
        ContradictionFinding(
            clause_a_title="Intellectual Property Ownership",
            clause_b_title="Termination for Convenience",
            contradiction_type="Logical Conflict",
            severity=RiskLevel.HIGH,
            description=(
                "Clause A says IP transfers to Client upon full payment. "
                "Clause B says the Vendor may terminate with 7 days notice and collect a termination fee. "
                "These conflict because early termination before full payment leaves ownership undefined."
            ),
            impact="Either party could claim ownership of all work product after early termination.",
        ),
        ContradictionFinding(
            clause_a_title="Payment Terms",
            clause_b_title=None,
            contradiction_type="Self-Defeating",
            severity=RiskLevel.MEDIUM,
            description=(
                "The payment clause states the Client may not withhold payment for any reason including "
                "quality disputes, yet also grants the Client the right to dispute deliverables. "
                "These cannot both be true: the dispute right is meaningless if payment cannot be withheld."
            ),
            impact="The Client has no practical financial leverage to enforce quality of deliverables.",
        ),
    ],
    clauses=[
        ClauseAnalysis(
            clause_title="Limitation of Liability",
            clause_type="Liability",
            original_text=(
                "In no event shall the Vendor be liable for any indirect, incidental, special, "
                "or consequential damages. The Vendor's total liability shall not exceed the amount "
                "paid in the preceding thirty (30) days."
            ),
            category=ClauseCategory.HIGH_RISK,
            risk_level=RiskLevel.HIGH,
            risk_score=75,
            affected_party=AffectedParty.CLIENT,
            what_works_well="Consequential damages exclusion is standard in commercial agreements.",
            risk_explanation=(
                "The 30-day liability cap is far below commercial standard. "
                "Most service agreements use 12 months of fees. "
                "This leaves the Client with minimal recourse after a major service failure."
            ),
            suggested_revision=(
                "The Vendor's total aggregate liability shall not exceed the total fees paid in the "
                "preceding twelve (12) months. The consequential damages exclusion shall not apply "
                "in cases of gross negligence, wilful misconduct, or data breach."
            ),
            negotiation_advice=(
                "Push for a 12-month fee cap. Request carve-outs for data breaches, IP infringement, "
                "and wilful misconduct."
            ),
            enforceability_concern=True,
        ),
        ClauseAnalysis(
            clause_title="Intellectual Property Ownership",
            clause_type="Intellectual Property",
            original_text=(
                "All work product, inventions, and developments created by Vendor, including any "
                "pre-existing tools, frameworks, or methodologies used in delivery, shall become "
                "the exclusive property of the Client upon full payment."
            ),
            category=ClauseCategory.HIGH_RISK,
            risk_level=RiskLevel.HIGH,
            risk_score=72,
            affected_party=AffectedParty.PROVIDER,
            what_works_well="Clear trigger event (full payment) for IP transfer.",
            risk_explanation=(
                "Transferring pre-existing Vendor tools and frameworks to the Client is non-standard "
                "and will prevent the Vendor from using their own technology in future work. "
                "This creates delivery risk and is unlikely to be accepted as written."
            ),
            suggested_revision=(
                "Client shall own all custom work product created specifically for this engagement. "
                "Vendor retains ownership of pre-existing tools and frameworks and grants Client a "
                "perpetual, non-exclusive license for use within the delivered product."
            ),
            negotiation_advice=(
                "Distinguish bespoke deliverables from pre-existing IP. "
                "Request an explicit license grant for any Vendor IP embedded in the product."
            ),
        ),
        ClauseAnalysis(
            clause_title="Termination for Convenience",
            clause_type="Termination",
            original_text=(
                "Either party may terminate this Agreement for convenience upon seven (7) days "
                "written notice. Upon termination, Client shall pay for all work completed to date "
                "plus a termination fee equal to 25% of the remaining contract value."
            ),
            category=ClauseCategory.HIGH_RISK,
            risk_level=RiskLevel.HIGH,
            risk_score=70,
            affected_party=AffectedParty.CLIENT,
            what_works_well="Mutual termination right is fair in principle.",
            risk_explanation=(
                "7 days is an unusually short notice period for a complex development engagement. "
                "The 25% termination fee on remaining contract value creates a significant financial "
                "penalty even if the Vendor has underperformed."
            ),
            suggested_revision=(
                "Either party may terminate for convenience upon 30 days written notice. "
                "Client shall pay for work completed and approved to date. "
                "No termination fee shall apply where termination follows a material breach by Vendor."
            ),
            negotiation_advice=(
                "Negotiate notice to 30 days minimum. Challenge the termination fee — limit to "
                "documented costs incurred, and waive if Vendor is in breach."
            ),
        ),
        ClauseAnalysis(
            clause_title="Payment Terms",
            clause_type="Payment",
            original_text=(
                "Client shall pay all invoices within fifteen (15) days of receipt. Late payments "
                "shall accrue interest at 2% per month. Client may not withhold payment for any reason, "
                "including disputes regarding deliverable quality."
            ),
            category=ClauseCategory.MODERATE_RISK,
            risk_level=RiskLevel.MEDIUM,
            risk_score=52,
            affected_party=AffectedParty.CLIENT,
            what_works_well="Fixed payment terms and interest on late payment provide commercial certainty.",
            risk_explanation=(
                "Prohibiting payment withholding even during quality disputes removes the Client's "
                "main leverage. The 2% monthly interest (24% annually) is above market standard."
            ),
            suggested_revision=(
                "Client shall pay undisputed invoices within 30 days. Client may withhold payment "
                "for genuinely disputed deliverables pending resolution. Late interest shall not "
                "exceed 1% per month on undisputed amounts."
            ),
            negotiation_advice=(
                "Push for 30-day terms, the right to withhold on disputed items, and reduce "
                "interest to 1% per month."
            ),
        ),
        ClauseAnalysis(
            clause_title="Non-Solicitation",
            clause_type="Non-compete",
            original_text=(
                "During the term and for two (2) years following termination, Client agrees not to "
                "hire or contract with any employee or subcontractor of Vendor, globally."
            ),
            category=ClauseCategory.MODERATE_RISK,
            risk_level=RiskLevel.MEDIUM,
            risk_score=48,
            affected_party=AffectedParty.CLIENT,
            enforceability_concern=True,
            what_works_well="Mutual non-solicitation protects both parties' workforce investments.",
            risk_explanation=(
                "Two years globally applying to all Vendor staff and subcontractors is broader than "
                "standard. Enforceability of global scope is uncertain in most jurisdictions."
            ),
            suggested_revision=(
                "During the term and for 12 months following termination, Client shall not directly "
                "solicit Vendor employees with whom they had material contact, limited to jurisdictions "
                "where services were delivered."
            ),
            negotiation_advice=(
                "Reduce to 12 months, limit to direct solicitation, and restrict geography."
            ),
        ),
        ClauseAnalysis(
            clause_title="Confidentiality",
            clause_type="Confidentiality",
            original_text=(
                "Each party agrees to keep confidential all information designated as confidential "
                "by the disclosing party. This obligation shall survive termination for three (3) years."
            ),
            category=ClauseCategory.ACCEPTABLE_STANDARD,
            risk_level=RiskLevel.LOW,
            risk_score=18,
            affected_party=AffectedParty.BOTH,
            what_works_well=(
                "Mutual obligations, clear 3-year survival, and standard marking requirement "
                "are commercially normal."
            ),
            risk_explanation="Minor: no catch-all for obviously sensitive unmarked information.",
            suggested_revision=(
                "Optionally add that information a reasonable person would understand to be "
                "confidential is protected even without explicit marking."
            ),
            negotiation_advice="This clause is acceptable as-is. The marking requirement is standard.",
        ),
    ],
)


def get_mock_analysis() -> ContractAnalysis:
    return MOCK_ANALYSIS
