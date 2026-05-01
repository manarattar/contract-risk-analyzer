"""
Three reference contracts for calibration testing.
"""

BAD_CONTRACT = """
SERVICE AGREEMENT
This Agreement is made between The Client and The Provider on today's date.

1. Work
The Provider will do the work that the Client wants. The work may include design, development,
consulting, marketing, writing, support, and other things as needed.

2. Payment
The Client will pay the Provider a fair amount after the work is mostly finished.
Payment should be made soon, unless the Client is not satisfied.
The Provider may charge extra if the work is harder than expected.

3. Timeline
The Provider will try to finish the work quickly. The Client understands that delays may happen.
No exact delivery date is guaranteed, but the work should be completed within a reasonable time.

4. Changes
The Client can request unlimited changes. The Provider may refuse changes that are too much.
If changes are requested, the price may or may not increase depending on the situation.

5. Ownership
The Client owns the work after payment. The Provider also owns anything created during the project
and may use it for other clients. Both parties can use the materials however they want.

6. Confidentiality
Both parties agree not to share secret information unless they need to, want to, or are asked
by someone important.

7. Termination
Either party can end this Agreement at any time for any reason.
If the Agreement ends, the Client may still need to pay something, but only if the Provider deserves it.

8. Liability
The Provider is not responsible for any damages, problems, losses, errors, delays, security issues,
or anything else that happens, even if caused by the Provider.

9. Warranties
The Provider promises the work will be good, but does not guarantee that it will work, be correct,
be legal, or meet the Client's needs.

10. Disputes
If there is a dispute, the parties will talk about it. If they cannot agree, they may go to court
or arbitration or another process depending on what seems best.

11. Governing Law
This Agreement is governed by the laws of the place where the work happens or where one of the
parties lives.

12. Entire Agreement
This Agreement is the full agreement, except for emails, messages, verbal promises, assumptions,
earlier discussions, and anything both parties understood.

Signed,
Client: ______________________  Provider: ______________________
"""

GOOD_CONTRACT = """
SOFTWARE DEVELOPMENT SERVICES AGREEMENT

This Software Development Services Agreement ("Agreement") is entered into as of January 1, 2025
("Effective Date") by and between Acme Corp, a Delaware corporation ("Client"), and DevPro Ltd,
a UK private limited company ("Provider").

1. Services
Provider shall deliver the software deliverables described in Schedule A ("Deliverables") in
accordance with the specifications set out therein. Any changes to the scope must be submitted
in writing via a Change Request Form and approved by both parties before work commences.

2. Payment
Client shall pay Provider GBP 15,000 per milestone as set out in Schedule B. Payment is due within
30 days of receipt of a valid invoice. Late payments shall accrue interest at 1.5% per month on
overdue amounts. Client may withhold payment for genuinely disputed deliverables pending resolution,
provided Client notifies Provider in writing within 5 business days of invoice receipt.

3. Delivery and Acceptance
Provider shall deliver each milestone by the dates specified in Schedule B. Client shall have
14 days following delivery to review and either (a) accept the Deliverable in writing, or
(b) provide a written list of defects. Provider shall correct confirmed defects within 14 days
at no additional charge.

4. Intellectual Property
All custom Deliverables created specifically for Client under this Agreement shall be owned by
Client upon full payment of fees. Provider retains ownership of all pre-existing tools, libraries,
frameworks, and methodologies ("Provider IP") and grants Client a perpetual, royalty-free,
non-exclusive licence to use Provider IP solely as incorporated in the Deliverables.

5. Confidentiality
Each party ("Receiving Party") shall hold in confidence all non-public information disclosed by
the other party ("Disclosing Party") that is marked as confidential or that a reasonable person
would understand to be confidential ("Confidential Information"). Confidential Information shall
not be disclosed except: (a) with prior written consent; (b) to employees or contractors who need
to know and are bound by equivalent obligations; or (c) as required by law, court order, or
regulatory authority, provided the Receiving Party gives prior written notice where legally permitted.
This obligation survives termination for five years.

6. Liability
Provider's total aggregate liability for any claims under or in connection with this Agreement
shall not exceed the total fees paid by Client in the twelve (12) months preceding the event
giving rise to the claim. The foregoing limitation shall not apply in cases of gross negligence,
wilful misconduct, fraud, or breach of confidentiality obligations.

7. Termination
Either party may terminate this Agreement for convenience on 30 days' written notice.
Either party may terminate immediately on written notice if the other commits a material breach
that remains unremedied for 14 days after written notice. On termination, Client shall pay for
all accepted Deliverables delivered up to the termination date; no further amounts shall be owed.

8. Dispute Resolution
Any dispute arising under this Agreement shall first be referred to senior representatives of
each party for good-faith resolution. If unresolved within 20 business days, the dispute shall
be submitted to binding arbitration under the LCIA Rules in London, England. The arbitration
shall be conducted in English by a sole arbitrator. This clause does not prevent either party
from seeking urgent injunctive relief from a competent court.

9. Governing Law
This Agreement is governed by and construed in accordance with the laws of England and Wales.
The parties irrevocably submit to the exclusive jurisdiction of the courts of England and Wales
for matters not subject to arbitration.

10. Warranties
Provider warrants that: (a) the Deliverables shall materially conform to the specifications in
Schedule A for 90 days following acceptance; (b) Provider has the right to grant the licences
and assignments set out herein; and (c) the Deliverables shall not infringe any third-party
intellectual property rights.

11. Entire Agreement
This Agreement, together with its Schedules, constitutes the entire agreement between the parties
with respect to its subject matter and supersedes all prior written and oral agreements. No amendment
shall be effective unless in writing and signed by authorised representatives of both parties.

Signed,
Client: ______________________  Provider: ______________________
"""

INCOMPLETE_CONTRACT = """
FREELANCE DEVELOPMENT AGREEMENT

This Agreement is between StartupCo ("Client") and Jane Smith ("Developer") effective March 1, 2025.

1. Work
Developer will build a mobile application as described in the attached brief. Specific features
include user authentication, payment processing, and a dashboard. The parties may agree additional
features in writing.

2. Payment
Client shall pay Developer USD 8,000 in two instalments: USD 4,000 on signing and USD 4,000 on
final delivery. All payments are due within 14 days of the applicable milestone.

3. Timeline
Developer shall use reasonable endeavours to complete the application by June 30, 2025.
Both parties acknowledge that software development timelines may shift due to technical complexity.

4. Intellectual Property
All code and materials produced under this Agreement shall be owned by Client upon receipt of full
payment. Developer retains the right to include the project in her portfolio.

5. Confidentiality
Developer shall keep Client's business information, user data, and product plans confidential
during and for two years after this Agreement. Developer shall not use Client's information for
any purpose other than performing the services.

6. Termination
Either party may terminate this Agreement on 14 days' written notice. On termination, Client
shall pay for work completed and accepted to date on a pro-rata basis.

7. Governing Law
This Agreement is governed by the laws of the State of California, USA.

Signed,
Client: ______________________  Developer: ______________________
"""
