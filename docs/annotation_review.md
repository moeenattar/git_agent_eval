# Draft Annotation Review

These 50 records are proposed labels for review, not frozen ground truth. They contain 40 real GitHub issues and 10 synthetic coverage cases. The split is 15 calibration cases and 35 golden-test cases.

## Review instructions

For each row, read the title and the full body in the corresponding JSONL record. For real cases, the ID links to GitHub for convenience, but make the label decision from title and body only. Do not use repository labels, comments, issue state, or resolution as annotation evidence.

In the Review notes column, write one of:

- `agree`
- a proposed value such as `priority=medium`
- a short question or disagreement

Pay particular attention to every `high` case, every security case, and cases marked for human review. After review, update the JSONL records, run validation, and only then change `dataset_version` from `draft-v0` to `v1`.

## Coverage summary

| Dimension | Distribution |
|---|---|
| Source | 40 real, 10 synthetic |
| Split | 15 calibration, 35 golden test |
| Issue type | 23 bug, 10 enhancement, 9 maintenance, 7 documentation, 1 other |
| Priority | 12 high, 21 medium, 17 low |
| Human review | 25 yes, 25 no |

## Cases

| Split | ID | Title | Type | Priority | Human | Draft rationale | Review notes |
|---|---|---|---|---|---|---|---|
| calibration | [python-pythondotorg-3100](https://github.com/python/pythondotorg/issues/3100) | Bug: Typo on release pages for Python 3.14.6 and 3.14.7 | documentation | low | no | A specific public-content typo is identified, has low impact, and includes an exact correction. |  |
| calibration | [python-pythondotorg-3094](https://github.com/python/pythondotorg/issues/3094) | Bug: Nominee list shows nominations of you, not nominations you made, and ignores the election | bug | medium | no | The election nominee query returns incorrect cross-election data and broken detail links, with complete reproduction and cause information. |  |
| calibration | [python-pythondotorg-3070](https://github.com/python/pythondotorg/issues/3070) | Bug: Contrast too low for PPC election form title | bug | medium | no | The election form violates a stated WCAG contrast requirement, creating a meaningful accessibility barrier with a specific remedy. |  |
| calibration | [python-pythondotorg-3059](https://github.com/python/pythondotorg/issues/3059) | Enhancement: Add Juno to the "Python for iOS and iPadOS" section on /download/other/ | enhancement | low | yes | This requests adding a commercial IDE to a curated page; impact is low and inclusion requires a maintainer content-policy decision. |  |
| calibration | [python-pythondotorg-3047](https://github.com/python/pythondotorg/issues/3047) | Hardening: [low-priority] Remove User.api_v2_token property (returns plaintext API token) | maintenance | high | yes | Removing an unused plaintext credential accessor is security hardening; credential exposure risk requires prompt specialist review even though no current leak is shown. |  |
| calibration | [python-pythondotorg-3046](https://github.com/python/pythondotorg/issues/3046) | Bug: Search result templates apply `\|safe` to `striptags` output | bug | high | yes | User-influenced search content is marked safe despite an explicitly fragile sanitization invariant, making this a potential injection issue requiring security review. |  |
| calibration | [python-pythondotorg-3023](https://github.com/python/pythondotorg/issues/3023) | Bug: Table on main download page doesn't have a Python 3.15 entry | bug | medium | no | A current Python version is missing from the primary downloads table, a clear functional content-generation defect with noticeable user impact. |  |
| calibration | [python-pythondotorg-3009](https://github.com/python/pythondotorg/issues/3009) | Enhancement: Review the site style | enhancement | low | yes | A broad visual redesign is non-urgent and requires subjective product, brand, and scope decisions. |  |
| calibration | [python-pythondotorg-2990](https://github.com/python/pythondotorg/issues/2990) | Bug: Redis connection pool exhaustion on /downloads/ endpoint under high concurrency | bug | high | yes | Potential connection-pool exhaustion could degrade a high-traffic download endpoint, but the supplied production error is explicitly an unverified example. |  |
| calibration | [python-pythondotorg-2983](https://github.com/python/pythondotorg/issues/2983) | Bug: Broken call to action on the Volunteer page | documentation | medium | yes | The primary volunteer call to action is unusable, but the reporter cannot establish the correct replacement channel. |  |
| calibration | [python-pythondotorg-2887](https://github.com/python/pythondotorg/issues/2887) | Bug: Sponsor logo collides with section header text | bug | low | no | A reproducible sponsor-page logo overlap is a localized cosmetic layout defect. |  |
| calibration | [python-pythondotorg-2869](https://github.com/python/pythondotorg/issues/2869) | Bug(CI): CI duplication and messiness | maintenance | low | no | Duplicate successful CI runs waste resources and create confusion but do not break production functionality. |  |
| calibration | synthetic-cal-001 | Contributor guide setup link returns 404 | documentation | low | no | A specific documentation defect has a clear correction and low impact. |  |
| calibration | synthetic-cal-002 | Login endpoint returns 500 for all users after deployment | bug | high | no | A confirmed major regression blocks all users and includes a reproducible rollback signal. |  |
| calibration | synthetic-cal-003 | Maybe improve profiles | enhancement | low | yes | The request suggests an improvement but lacks desired behavior and impact evidence. |  |
| golden | [python-pythondotorg-3041](https://github.com/python/pythondotorg/issues/3041) | Proposal: add a site-wide Content-Security-Policy (Report-Only first) | enhancement | high | yes | A site-wide CSP is security hardening with unresolved allowlists, rollout, and reporting decisions that require maintainers. |  |
| golden | [python-pythondotorg-3034](https://github.com/python/pythondotorg/issues/3034) | Harden sponsors admin actions: require change permission and make lock POST-only | maintenance | high | yes | Admin authorization gaps and state mutation over GET are security-sensitive hardening work requiring specialist review. |  |
| golden | [python-pythondotorg-3012](https://github.com/python/pythondotorg/issues/3012) | Bug: release-file bulk deletion can leave files behind | bug | medium | no | A bulk-delete endpoint reports success while leaving stale release-file records, creating meaningful automation and metadata integrity impact. |  |
| golden | [python-pythondotorg-2996](https://github.com/python/pythondotorg/issues/2996) | Enhancement: Separate audit log for privileged requests | enhancement | medium | yes | Long-retention privileged-request logging is operationally meaningful but needs decisions about retention, privacy, and exact scope. |  |
| golden | [python-pythondotorg-2982](https://github.com/python/pythondotorg/issues/2982) | Enhancement: Big obvious download button for https://www.python.org/ftp/python/doc/3.14.0/ | enhancement | low | no | This is a clear, non-urgent discoverability improvement for offline documentation downloads. |  |
| golden | [python-pythondotorg-2981](https://github.com/python/pythondotorg/issues/2981) | Incorrect Content-Encoding header on .bz2 files breaks proxy downloads | bug | medium | no | An incorrect response header prevents a defined user segment behind inspecting proxies from downloading release archives. |  |
| golden | [python-pythondotorg-2971](https://github.com/python/pythondotorg/issues/2971) | Sponsor Helpscout Integration | enhancement | low | yes | A Help Scout integration is requested, but the one-line report lacks workflow, data, privacy, and acceptance details. |  |
| golden | [python-pythondotorg-2895](https://github.com/python/pythondotorg/issues/2895) | Migrate from minio to s3 native (or something) | maintenance | medium | yes | A deprecated storage component needs migration, but the target technology and production constraints remain undecided. |  |
| golden | [python-pythondotorg-2891](https://github.com/python/pythondotorg/issues/2891) | https://www.python.org/api/v2/downloads/release/ endpoint returns error | bug | medium | no | The downloads API is consistently throttled for ordinary access and breaks dependency automation, with a direct reproduction. |  |
| golden | [python-pythondotorg-2865](https://github.com/python/pythondotorg/issues/2865) | Bug: Dead "Release notes" links on the download page for old releases | documentation | low | no | Release-note links for older versions are broken, a specific low-impact documentation navigation defect. |  |
| golden | [python-pythondotorg-2847](https://github.com/python/pythondotorg/issues/2847) | Bug: Downloading mail archives from Mailman3 often times out | bug | medium | no | Mail archive exports repeatedly time out even for small ranges, preventing a supported research workflow with clear reproduction. |  |
| golden | [python-pythondotorg-2829](https://github.com/python/pythondotorg/issues/2829) | Enhancement: add sha256 field for release | enhancement | medium | yes | Adding SHA-256 metadata is a meaningful release-integrity improvement, but the terse body delegates essential context to external links. |  |
| golden | [python-pythondotorg-2814](https://github.com/python/pythondotorg/issues/2814) | Bug: 503 on some pages | bug | medium | yes | A documentation page returns 503 in several browsers but succeeds with curl, so the meaningful availability symptom needs environment investigation. |  |
| golden | [python-pythondotorg-2787](https://github.com/python/pythondotorg/issues/2787) | Bug: Feedburner Feed seems to contain SPAM | bug | high | yes | An official-looking feed distributing unexpected spam may indicate account or feed compromise and requires immediate security review. |  |
| golden | [python-pythondotorg-2752](https://github.com/python/pythondotorg/issues/2752) | Bug: Website SSL certificates invalid for some server IPv6 addresses | bug | high | yes | An invalid TLS certificate blocks documentation access for users routed to an affected IPv6 address and requires infrastructure/security review. |  |
| golden | [python-pythondotorg-2750](https://github.com/python/pythondotorg/issues/2750) | Docs: document Downloads API | documentation | low | no | The existing Downloads API lacks public documentation; the requested documentation outcome is clear and non-urgent. |  |
| golden | [python-pythondotorg-2743](https://github.com/python/pythondotorg/issues/2743) | Tests: Investigate `OrderedModelManager` warning for Sponsor models | maintenance | low | no | This asks to investigate non-failing model-manager test warnings, which is routine engineering cleanup. |  |
| golden | [python-pythondotorg-2739](https://github.com/python/pythondotorg/issues/2739) | Bug: Outbound links take 5+ seconds to navigate to | bug | medium | no | Outbound navigation is delayed by more than five seconds for users with a common blocker, with a reproduction and likely component. |  |
| golden | [python-pythondotorg-2729](https://github.com/python/pythondotorg/issues/2729) | Bug: broken image links on "Using Python to Automate Tedious Tasks" success story page | documentation | low | no | Images on one success-story page are inaccessible because their asset URLs return AccessDenied. |  |
| golden | [python-pythondotorg-2724](https://github.com/python/pythondotorg/issues/2724) | Enhancement: Sanitize release names to require string | enhancement | medium | no | Admin-side release-name validation would prevent invalid records from crashing a downloads page; the proposed behavior and validation are specific. |  |
| golden | [python-pythondotorg-2723](https://github.com/python/pythondotorg/issues/2723) | Bug: Events page shows events in wrong order | bug | medium | no | The public events page presents events in the wrong chronological order, a clear functional UX defect. |  |
| golden | [python-pythondotorg-2709](https://github.com/python/pythondotorg/issues/2709) | Enhancement: Django 5.2 | maintenance | medium | yes | A major framework upgrade is important maintenance, but compatibility work and impact still need investigation. |  |
| golden | [python-pythondotorg-2700](https://github.com/python/pythondotorg/issues/2700) | Bug: docs.python.org certificate is expired | bug | high | yes | The documentation service is returning 503 with certificate-related evidence, creating a broad availability and TLS concern. |  |
| golden | [python-pythondotorg-2681](https://github.com/python/pythondotorg/issues/2681) | Bug: Remote get shell | bug | high | yes | The report alleges possible container escape and privilege escalation; its validity is uncertain but the security impact requires specialist review. |  |
| golden | [python-pythondotorg-2677](https://github.com/python/pythondotorg/issues/2677) | Bug: Resolutions in PSF minutes not listed on Resolutions page | documentation | low | no | Approved resolutions are missing from a central records page despite appearing in the minutes, a specific content synchronization problem. |  |
| golden | [python-pythondotorg-2664](https://github.com/python/pythondotorg/issues/2664) | Bug: gzipped and tarball for 3.10.15 source code have incorrect permissions | bug | medium | no | Both source archives for a Python release return 403, blocking that release's source download with clear reproduction. |  |
| golden | [python-pythondotorg-2651](https://github.com/python/pythondotorg/issues/2651) | Investigate logs forwarding to Datadog after IaC conversion | maintenance | medium | yes | A configuration change sends all logs rather than rate-limit events to Datadog, but scope, privacy, and cost impact need investigation. |  |
| golden | [python-pythondotorg-2599](https://github.com/python/pythondotorg/issues/2599) | Deps: update to elasticsearch8 | maintenance | low | yes | The dependency upgrade identifies configuration locations but omits motivation, compatibility requirements, and acceptance criteria. |  |
| golden | synthetic-test-001 | Password reset tokens exposed in analytics events | bug | high | yes | Production behavior exposes security credentials and requires specialist review. |  |
| golden | synthetic-test-002 | Update CI action to the supported major version | maintenance | low | no | This is planned dependency maintenance with no current functional impact. |  |
| golden | synthetic-test-003 | Search returns no results for accented names | bug | medium | no | A clear functional defect affects a user segment and has a workaround. |  |
| golden | synthetic-test-004 | Choose whether organization names should be public | enhancement | medium | yes | The proposed capability has privacy implications and requires a product policy decision. |  |
| golden | synthetic-test-005 | CSV export deletes customer records after download | bug | high | no | A confirmed production regression causes data loss and has clear reproduction and containment details. |  |
| golden | synthetic-test-006 | Save button does not work, although saving succeeds | bug | medium | yes | There is a clear save-status defect, but contradictory persistence evidence and unconfirmed data loss require review. |  |
| golden | synthetic-test-007 | Please help with my conference ticket invoice | other | low | yes | This is an account-specific support request rather than a software issue and needs human routing. |  |
