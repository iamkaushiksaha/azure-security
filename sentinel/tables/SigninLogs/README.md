# SigninLogs

> **Category:** Microsoft Entra ID (Azure Resources, Security)
> **Connector / source:** Microsoft Entra ID diagnostic settings → "SignInLogs" log category (interactive user sign-ins), streamed to Log Analytics / Microsoft Sentinel. Requires a Microsoft Entra ID P1/P2 licence to export.
> **Table plan:** Analytics (default). Basic logs supported (the reference flags **Basic log: Yes**); also supports ingestion-time DCR transforms and lake-only ingestion.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs

## What this table is
Each row is a single **interactive** sign-in to Microsoft Entra ID (Azure AD) — a user presenting an authentication factor (password, MFA response, passkey, etc.) to access an application or resource. Rows appear continuously, within minutes of the sign-in, for every interactive authentication attempt whether it succeeds or fails. In a SOC this is the primary table for **identity attack detection**: failed-then-success brute force / password spray, impossible-travel and anonymizer (Tor/VPN) sign-ins, risky sign-ins surfaced by Entra ID Protection, MFA fatigue, and legacy-protocol authentication. Non-interactive token redemptions live in the sibling `AADNonInteractiveUserSignInLogs` table, not here.

**Underlying Graph model:** these rows are the Log Analytics projection of the Microsoft Graph `signIn` resource (`microsoft.graph/tenants`). The nested objects from Graph become the dynamic/JSON columns here: Graph `status` → `Status` (`errorCode`, `failureReason`), `deviceDetail` → `DeviceDetail` (`deviceId`, `operatingSystem`, `browser`, `isCompliant`), `location` (`signInLocation`) → `LocationDetails` (`city`, `state`, `countryOrRegion`, `geoCoordinates`), and the authentication-method breakdown → `AuthenticationDetails`. Graph `riskLevelDuringSignIn` / `riskState` / `riskEventTypes_v2` map straight to the same-named columns, and Graph's numeric `status.errorCode` is what surfaces as the string `ResultType`.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. Dynamic (nested JSON) columns are marked **dyn**.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the record was ingested (use for time filtering). |
| CreatedDateTime | datetime | When the sign-in was initiated (event time), UTC. |
| Id | string | Identifier of the sign-in activity. |
| AADTenantId | string | Tenant ID the sign-in occurred in. |
| Identity | string | Display name of the actor identified in the sign-in. |
| UserPrincipalName | string | UPN of the user. Always lowercase; for guests stored in "true" format. |
| UserDisplayName | string | Display name of the user. |
| UserId | string | GUID of the user object. |
| UserType | string | `member` or `guest`. |
| AlternateSignInName | string | Identifier the user typed to sign in (may differ from UPN). |
| SignInIdentifier | string | Identification the user provided to sign in. |
| SignInIdentifierType | string | `userPrincipalName`, `phoneNumber`, `proxyAddress`, `qrCode`, `onPremisesUserPrincipalName`. |
| AppId | string | Application (client) ID in Entra ID. |
| AppDisplayName | string | Application name shown in the portal. |
| AppOwnerTenantId | string | Tenant ID of the application owner. |
| ResourceId | string | ID of the resource the user signed in to. |
| ResourceDisplayName | string | Name of the resource the user signed in to. |
| ResourceIdentity | string | The resource the user signed in to. |
| ResourceTenantId | string | Tenant ID of the referenced resource. |
| ResourceServicePrincipalId | string | Service principal ID of the target resource. |
| ServicePrincipalId | string | App identifier used for sign-in (populated for app sign-ins). |
| ServicePrincipalName | string | App name used for sign-in (populated for app sign-ins). |
| IPAddress | string | Client IP address the sign-in came from. |
| IPAddressFromResourceProvider | string | IP a user used to reach a resource provider (often null). |
| GlobalSecureAccessIpAddress | string | Source IP when routed via Global Secure Access. |
| AutonomousSystemNumber | string | **ASN** of the network the actor used (string, not int). |
| Location | string | Two-letter country/region code of the sign-in. |
| LocationDetails | **dyn** | City, state, country/region, and `geoCoordinates` (lat/long). |
| NetworkLocationDetails | string | Network location details (type and named networks). |
| IsInteractive | bool | Whether the sign-in is interactive (this table = interactive). |
| ClientAppUsed | string | Legacy/modern client: `Browser`, `Mobile Apps and Desktop clients`, `Exchange ActiveSync`, `IMAP`, `MAPI`, `SMTP`, `POP`, `Modern clients`, `other clients`. |
| UserAgent | string | User-agent string of the sign-in. |
| ResultType | string | **5–6 digit Entra error code as a STRING. `"0"` = success;** any other value is a failure. |
| ResultSignature | string | Result signature for the sign-in. |
| ResultDescription | string | Error message / reason for failure. |
| Status | **dyn** | Sign-in status object: `errorCode`, `failureReason`, `additionalDetails`. |
| AuthenticationRequirement | string | Highest auth level needed: `singleFactorAuthentication` / `multiFactorAuthentication`. |
| AuthenticationRequirementPolicies | string | Sources of the auth requirement (CA, per-user MFA, Identity Protection, security defaults). |
| AuthenticationDetails | string | **JSON-holding string**: per-step auth methods and whether each `succeeded`. |
| AuthenticationMethodsUsed | string | Methods used: SMS, Authenticator App, App Verification code, Password, FIDO, PTA, PHS. |
| AuthenticationProcessingDetails | string | Extra processing details (e.g. PTA/PHS agent, federation server/farm). |
| AuthenticationProtocol | string | `none`, `oAuth2`, `ropc`, `wsFederation`, `saml20`, `deviceCode`. |
| AuthenticationContextClassReferences | string | CA authentication contexts applied to the sign-in. |
| ConditionalAccessStatus | string | `success`, `failure`, or `notApplied`. |
| ConditionalAccessPolicies | **dyn** | CA policies triggered by the sign-in. |
| AppliedConditionalAccessPolicies | string | Applied CA policy details (string projection). |
| ConditionalAccessAudiences | string | Audiences targeted by the CA policy. |
| SessionId | string | Session ID generated during the sign-in. |
| SessionLifetimePolicies | string | CA session-management policies applied. |
| CorrelationId | string | Client-sent correlation ID (key for cross-table joins). |
| OriginalRequestId | string | Request ID of the first request in the auth sequence. |
| UniqueTokenIdentifier | string | Base64 request identifier tracking issued tokens. |
| IncomingTokenType | string | Token type used to sign in (e.g. primary refresh token, SAML assertion). |
| TokenIssuerName | string | Identity provider name (e.g. sts.microsoft.com). |
| TokenIssuerType | string | `AzureAD`, `ADFederationServices`, `AzureADBackupAuth`, etc. |
| TokenProtectionStatusDetails | **dyn** | Whether the sign-in token was bound to the device. |
| IsRisky | bool | Whether the sign-in is flagged risky. |
| RiskState | string | `none`, `confirmedSafe`, `remediated`, `dismissed`, `atRisk`, `confirmedCompromised`. |
| RiskDetail | string | Reason for the risk state (P2 only; else `hidden`). |
| RiskLevelDuringSignIn | string | **Risk at sign-in time: `none`, `low`, `medium`, `high`, `hidden`** (P2 only). |
| RiskLevelAggregated | string | Aggregated risk level (P2 only; else `hidden`). |
| RiskEventTypes_V2 | string | Risk event types: `unlikelyTravel`, `anonymizedIPAddress`, `maliciousIPAddress`, `unfamiliarFeatures`, `leakedCredentials`, `suspiciousIPAddress`, etc. |
| RiskEventTypes | string | **Deprecated** — use `RiskEventTypes_V2`. |
| MfaDetail | **dyn** | **Deprecated** MFA detail. |
| DeviceDetail | **dyn** | Device info: `deviceId`, `operatingSystem`, `browser`, `isCompliant`, `isManaged`, `trustType`. |
| FlaggedForReview | bool | User flagged the failed sign-in for admin review. |
| IsTenantRestricted | bool | Whether a tenant-restrictions policy applied. |
| IsThroughGlobalSecureAccess | bool | Whether the user came via Global Secure Access. |
| CrossTenantAccessType | string | Type of cross-tenant access used. |
| HomeTenantId | string | Tenant ID of the user initiating the sign-in. |
| HomeTenantName | string | Tenant name of the external home tenant. |
| ResourceOwnerTenantId | string | Tenant ID of the resource owner. |
| OriginalTransferMethod | string | Transfer method used to initiate the session. |
| ClientCredentialType | string | Client credential type (client assertion, client secret, …). |
| FederatedCredentialId | string | Federated credential ID. |
| SourceAppClientId | string | Source app's client ID for target identities. |
| Agent | **dyn** | Agentic sign-in property (`agentType`, `parentAppId`). |
| AppliedEventListeners | **dyn** | Logic Apps / Functions listeners triggered by the sign-in. |
| AuthenticationAppDeviceDetails | string | App/device state from the most recent authenticator step. |
| AuthenticationAppPolicyEvaluationDetails | string | Authenticator-app policy evaluation details. |
| AuthenticatorAppLocation | string | Location of the authenticator app. |
| DurationMs | long | Sign-in duration in milliseconds. |
| ProcessingTimeInMilliseconds | string | Server processing time. |
| Category | string | Diagnostic log category. |
| Level | string | Log level. |
| OperationName | string | Operation name (e.g. "Sign-in activity"). |
| OperationVersion | string | Operation version. |
| SourceSystem | string | Collecting agent type (e.g. `Azure`). |
| Type | string | Table name (`SigninLogs`). |

> Approximately **100 columns** total. Above lists every detection-relevant column individually. Trailing platform/billing columns are standard: `_BilledSize` (real), `_IsBillable` (string), `_ResourceId`, `Resource`, `ResourceGroup`, `ResourceProvider`, `OperationVersion`, `ResultSignature`, `ConditionalAccessAudiences`.

## Key columns for detection & hunting
- **Identity:** `UserPrincipalName` (lowercase UPN), `UserId` (GUID), `UserDisplayName`; `UserType` to split members vs guests.
- **Host / device:** no hostname — device identity is in `DeviceDetail`: `tostring(DeviceDetail.deviceId)`, `tostring(DeviceDetail.operatingSystem)`, `tostring(DeviceDetail.browser)`, `tobool(DeviceDetail.isCompliant)`.
- **Network:** `IPAddress` (source IP), `AutonomousSystemNumber` (ASN, string), `Location` (country code) and `LocationDetails` (city/geo).
- **Outcome / result:** `ResultType` — **STRING**, `"0"` = success, anything else is a failure code; human-readable reason in `ResultDescription` and `Status.failureReason`.
- **Timestamps:** `TimeGenerated` (ingestion) and `CreatedDateTime` (event/sign-in initiation).
- **Join keys (to other tables):** `UserPrincipalName` / `UserId` (→ AuditLogs, OfficeActivity, AADNonInteractiveUserSignInLogs, IdentityInfo), `IPAddress` (→ any network/threat-intel table), `CorrelationId` (→ AuditLogs for the action a sign-in led to), `AADTenantId`.

## ⚠️ Schema gotchas
- **`ResultType` is a STRING, not an int.** Success is the literal `"0"`. Filtering `where ResultType == 0` (numeric) silently fails — use `where ResultType == "0"` / `!= "0"`.
- **`Status`, `DeviceDetail`, `LocationDetails`, `ConditionalAccessPolicies`, `MfaDetail` are `dynamic`** — you must index/extract (`Status.errorCode`, `tostring(DeviceDetail.browser)`). `AuthenticationDetails`, `AuthenticationProcessingDetails` and `AppliedConditionalAccessPolicies` are typed `string` on the Learn page but still carry **JSON payloads**, so wrap with `parse_json()` before drilling in.
- **This table is interactive sign-ins only.** Non-interactive client/token sign-ins are in `AADNonInteractiveUserSignInLogs` (same shape). A brute-force or token-replay hunt that ignores the non-interactive twin will miss activity.
- **Risk columns are licence-gated.** `RiskLevelDuringSignIn`, `RiskLevelAggregated`, `RiskDetail`, `RiskState` only carry real values with Entra ID **P2**; otherwise they read `hidden`. Treat `hidden` as "unknown", not "safe".
- **Deprecated twins:** prefer `RiskEventTypes_V2` over `RiskEventTypes`; `MfaDetail` is deprecated.

## 🧪 Sample data
[`SigninLogs_sample.csv`](SigninLogs_sample.csv) — 20 rows. Tells the **Operation Quiet Ledger** identity-compromise step: `alexw@contoso.com` is brute-forced from Tor exit `185.220.101.2` (Amsterdam, NL, ASN 205100) at ~08:17–08:19, succeeds at **08:20**, then keeps accessing Azure Portal / SharePoint / Storage from the attacker IPs (incl. secondary `91.219.236.18`) — all with `RiskLevelDuringSignIn` escalating `low→medium→high` and `RiskState = atRisk` — against a backdrop of benign sign-ins from `meganb`, `jamest`, `itadmin`, `dvora`, `priya.menon` and the `svc-backup` automation account. This is the **08:20 risky sign-in** step of the cross-table scenario, feeding device logon on FIN-WS-07 and the later Azure/storage activity.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `UserPrincipalName`, `UserDisplayName`, `UserId`, `AppDisplayName`, `AppId`, `IPAddress`, `AutonomousSystemNumber`, `Location`, `LocationDetails`, `IsInteractive`, `ClientAppUsed`, `ResultType`, `ResultDescription`, `Status`, `DeviceDetail`, `AuthenticationDetails`, `AuthenticationRequirement`, `ConditionalAccessStatus`, `RiskLevelDuringSignIn`, `RiskState`, `RiskDetail`, `CorrelationId`, `AADTenantId`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Failed-then-success brute force from one IP — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** An account shows multiple password failures (`ResultType "50126"`) immediately followed by a success from the same source IP — credential guessing that landed.
```kusto
SigninLogs
| where TimeGenerated between (datetime(2026-06-10T08:00:00Z) .. datetime(2026-06-10T09:00:00Z))
| summarize
    Failures   = countif(ResultType == "50126"),
    Successes  = countif(ResultType == "0"),
    FirstFail  = minif(TimeGenerated, ResultType == "50126"),
    FirstOK    = minif(TimeGenerated, ResultType == "0")
    by UserPrincipalName, IPAddress, AutonomousSystemNumber
| where Failures >= 2 and Successes >= 1 and FirstOK > FirstFail
| order by Failures desc
```
**Triage:** True positive = failures then a success from a non-corporate ASN/geo (here ASN 205100, NL). Benign = a user fat-fingering a password then succeeding from a known corporate IP.

### H2 · Risky / anonymizer sign-in succeeded — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** Entra ID Protection rated a sign-in `medium`/`high` risk during sign-in and it still succeeded (`ResultType "0"`, `RiskState = atRisk`).
```kusto
SigninLogs
| where ResultType == "0"
| where RiskLevelDuringSignIn in ("medium", "high")
| where RiskState == "atRisk"
| project TimeGenerated, UserPrincipalName, IPAddress, Location,
          AutonomousSystemNumber, AppDisplayName, RiskLevelDuringSignIn,
          ConditionalAccessStatus, City = tostring(parse_json(LocationDetails).city)
| order by TimeGenerated asc
```
**Triage:** True positive = high-risk success from an unfamiliar country with Conditional Access `notApplied` (no MFA gate). Benign = low risk, or a known traveller whose session is later confirmed safe.

### H3 · Impossible travel — same user, two countries in a short window — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** One user signs in from two different countries within an hour — geographically impossible, indicating a shared/stolen credential.
```kusto
SigninLogs
| where ResultType == "0"
| summarize Countries = make_set(Location), IPs = make_set(IPAddress),
            Seen = count() by UserPrincipalName, bin(TimeGenerated, 1h)
| where array_length(Countries) > 1
| order by TimeGenerated asc
```
**Triage:** True positive = e.g. `alexw` from US and NL in the same hour. Benign = VPN egress that resolves to a neighbouring country, or one of the two being a non-interactive token (cross-check the non-interactive table).

### H4 · Sign-in from a non-compliant / unmanaged device — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** A successful sign-in came from a device that is not compliant and not managed — an attacker host rather than a corporate endpoint.
```kusto
SigninLogs
| where ResultType == "0"
| extend Dev = parse_json(DeviceDetail)
| where tobool(Dev.isCompliant) == false and tobool(Dev.isManaged) == false
| project TimeGenerated, UserPrincipalName, IPAddress, Location,
          OS = tostring(Dev.operatingSystem), Browser = tostring(Dev.browser),
          RiskLevelDuringSignIn, AppDisplayName
| order by TimeGenerated asc
```
**Triage:** True positive = unmanaged host + risky IP for a user who normally signs in from a compliant device. Benign = service/automation accounts (e.g. `svc-backup`) that legitimately have no device context.

## 🔗 Correlates with
- **AADNonInteractiveUserSignInLogs** on `UserPrincipalName` / `UserId` — the non-interactive twin; follow token redemptions after the interactive compromise.
- **AuditLogs** on `CorrelationId` (and `UserId`) — what the signed-in actor then *did* (role/group adds, app consent), e.g. the 09:40 privilege escalation.
- **DeviceLogonEvents / SecurityEvent** on the user (UPN → account) and timeline — pivot from the 08:20 cloud sign-in to the 08:35 device logon on `FIN-WS-07`.
- **AzureActivity** on `UserPrincipalName` / `IPAddress` — the 10:00 Azure role write and storage key-list actions from the same compromised identity/IP.

## 📚 References
- SigninLogs table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs
- Microsoft Graph `signIn` resource type (underlying property model) — https://learn.microsoft.com/en-us/graph/api/resources/signin?view=graph-rest-1.0
- Microsoft Entra sign-in error codes — https://login.microsoftonline.com/error
