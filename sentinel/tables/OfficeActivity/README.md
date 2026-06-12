# OfficeActivity

> **Category:** Security (Microsoft 365 / Office 365 unified audit log)
> **Connector / source:** Microsoft Sentinel **Office 365** data connector (Exchange, SharePoint, OneDrive, Teams, and Azure Active Directory record types from the Microsoft Purview / Office 365 Management Activity API)
> **Table plan:** Analytics (default) — the reference flags **Basic log: No**
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/officeactivity

## What this table is
Each row is one record from the **Office 365 unified audit log**: a single auditable action a user, admin, or service principal performed in a Microsoft 365 workload. The `OfficeWorkload` column tells you which service emitted it (Exchange, SharePoint, OneDrive, MicrosoftTeams, AzureActiveDirectory) and `RecordType` gives the finer audit-record class. Rows appear after the Office 365 connector pulls events from the Management Activity API, typically within minutes to an hour of the activity. In a SOC this is the primary table for **business email compromise** hunting (malicious inbox rules, mail forwarding, mailbox-permission grants) and **data-exfiltration** hunting (mass file downloads, anonymous links, external sharing from SharePoint/OneDrive).

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic, guid.)

| Column | Type | Description |
|---|---|---|
| AADGroupId | string | Azure Active Directory group id |
| AADTarget | string | The user that the action (identified by `Operation`) was performed on |
| Activity | string | The activity that the user performed |
| Actor | string | The user or service principal that performed the action |
| ActorContextId | string | The GUID of the organization that the actor belongs to |
| ActorIpAddress | string | The actor's IP address in IPv4 or IPv6 format (Azure AD / SharePoint record types) |
| AddOnGuid | string | Unique identifier of the add-on that generated this event |
| AddonName | string | Name of the add-on that generated this event |
| AddOnType | string | Type of add-on that generated this event |
| AffectedItems | string | Information about each item in the group |
| AppAccessContext | dynamic | Application context for the user or service principal that performed the action |
| AppDistributionMode | string | Application distribution mode |
| AppId | string | Application ID |
| Application | string | The application name |
| ApplicationId | string | SharePoint application ID |
| AppPoolName | string | The App pool name |
| ArtifactsShared | dynamic | The artifacts shared in the meeting |
| Attendees | dynamic | The list of attendees for the meeting |
| AzureActiveDirectory_EventType | string | The type of Azure AD event |
| AzureADAppId | string | Teams Application Azure AD ID |
| _BilledSize | real | The record size in bytes |
| ChannelGuid | string | Unique identifier for the channel being audited |
| ChannelName | string | Name of the channel being audited |
| ChannelType | string | Type of channel being audited (Standard/Private) |
| ChatName | string | The name of the chat |
| ChatThreadId | string | The Id of the chat thread |
| Client | string | Details about the client device, OS, and browser for the account login event |
| Client_IPAddress | string | The IP address of the device used when the **operation** was logged (Exchange mailbox actions) |
| ClientAppId | string | Client application ID |
| ClientInfoString | string | Information about the email client used to perform the operation |
| ClientIP | string | The IP address of the device used when the **activity** was logged (SharePoint/general) |
| ClientMachineName | string | The machine name that hosts the Outlook client |
| ClientProcessName | string | The email client used to access the mailbox |
| ClientVersion | string | The version of the email client |
| CommunicationType | string | The type of communications that was conducted |
| CrossMailboxOperations | bool | Indicates if the operation involved more than one mailbox |
| CustomEvent | string | Optional string for custom events |
| DataCenterSecurityEventType | int | The type of cmdlet event in lock box |
| DestFolder | string | The destination folder |
| DestinationFileExtension | string | File extension of a file that is copied or moved |
| DestinationFileName | string | Name of the file that is copied or moved |
| DestinationRelativeUrl | string | URL of the destination folder where a file is copied or moved |
| DestMailboxId | string | Set only if `CrossMailboxOperations` is True |
| DestMailboxOwnerMasterAccountSid | string | Set only if `CrossMailboxOperations` is True |
| DestMailboxOwnerSid | string | Set only if `CrossMailboxOperations` is True |
| DestMailboxOwnerUPN | string | Set only if `CrossMailboxOperations` is True |
| DeviceInformation | string | The user device information |
| EffectiveOrganization | string | Name of the tenant that the elevation/cmdlet was targeted at |
| ElevationApprovedTime | datetime | Timestamp for when the elevation was approved |
| ElevationApprover | string | The name of a Microsoft manager |
| ElevationDuration | int | Duration the elevation was active (hours) |
| ElevationRequestId | string | Unique identifier for the elevation request |
| ElevationRole | string | The role the elevation was requested for |
| ElevationTime | datetime | The start time of the elevation |
| Event_Data | string | Optional payload for custom events |
| EventSource | string | Identifies that an event occurred in SharePoint (`SharePoint` or `ObjectModel`) |
| ExtendedProperties | string | The extended properties of the Azure AD event |
| ExternalAccess | string | Specifies whether the cmdlet was run by a user in your organization |
| ExtraProperties | dynamic | A list of extra properties |
| Folder | string | The folder where a group of items is located |
| Folders | string | Information about the source folders involved in an operation |
| GenericInfo | string | Used for comments and other generic information |
| InternalLogonType | int | Reserved for internal use |
| InterSystemsId | string | GUID that tracks the actions across components within the Office 365 service |
| IntraSystemId | string | GUID generated by Azure AD to track the action |
| _IsBillable | string | Specifies whether ingesting the data is billable |
| IsJoinedFromLobby | bool | Whether the user joined from the lobby |
| IsManagedDevice | bool | Whether the operation was created by an org-managed device |
| Item | string | Represents the item upon which the operation was performed |
| ItemName | string | The string in the Subject field of the email message |
| ItemType | string | The type of object that was accessed or modified |
| JoinTime | datetime | The time the user joined the meeting |
| LeaveTime | datetime | The time the user left the meeting |
| ListItemUniqueId | string | The GUID of a uniquely identifiable list item |
| LoginStatus | int | From `OrgIdLogon.LoginStatus`; used to map logon failures |
| Logon_Type | string | Indicates the type of user who accessed the mailbox and performed the logged operation |
| LogonUserDisplayName | string | User-friendly name of the user who performed the operation |
| LogonUserSid | string | The SID of the user who performed the operation |
| MachineDomainInfo | string | Information about device sync operations |
| MachineId | string | Information about device sync operations |
| MailboxGuid | string | The Exchange GUID of the mailbox that was accessed |
| MailboxOwnerMasterAccountSid | string | Mailbox owner account's master account SID |
| MailboxOwnerSid | string | The SID of the mailbox owner |
| MailboxOwnerUPN | string | The email address of the person who owns the mailbox that was accessed |
| MeetingDetailId | string | The meeting detail ID |
| Members | dynamic | A list of users within a Team |
| MessageId | string | An identifier for a chat or channel message |
| ModifiedObjectResolvedName | string | User-friendly name of the object modified by the cmdlet |
| ModifiedProperties | string | Included for admin events (e.g. adding a site/site-collection admin) |
| Name | string | Only for settings events — name of the setting that changed |
| NewValue | string | Only for settings events — new value of the setting |
| OfficeId | string | Unique identifier of an audit record |
| OfficeObjectId | string | For SharePoint and OneDrive for Business activity — the full URL/path of the object |
| OfficeTenantId | string | The office tenant id |
| OfficeWorkload | string | The Office 365 service where the activity occurred (Exchange / SharePoint / OneDrive / MicrosoftTeams / AzureActiveDirectory) |
| OldValue | string | Only for settings events — old value of the setting |
| Operation | string | The name of the operation that the user performed |
| OperationProperties | dynamic | Additional operation properties |
| OperationScope | string | The scope the operation was performed on |
| OrganizationId | string | GUID for your organization's Office 365 tenant (constant per org) |
| OrganizationName | string | The name of the tenant |
| OriginatingServer | string | Name of the server from which the cmdlet was executed |
| Parameters | string | Name/value list of all parameters used with the cmdlet in `Operation` |
| RecordType | string | The type of operation indicated by the record (see AuditLogRecordType) |
| _ResourceId | string | Unique identifier for the resource the record is associated with |
| ResultReasonType | string | Reason for the result reported in `ResultStatus` |
| ResultStatus | string | Indicates whether the action in `Operation` was successful (e.g. `Succeeded`, `Failed`) |
| SendAsUserMailboxGuid | string | Exchange GUID of the mailbox accessed to send email as |
| SendAsUserSmtp | string | SMTP address of the user being impersonated |
| SendonBehalfOfUserMailboxGuid | string | Exchange GUID of the mailbox accessed to send mail on behalf of |
| SendOnBehalfOfUserSmtp | string | SMTP address of the user on whose behalf the email is sent |
| SensitivityLabelId | string | The current sensitivity label ID of the file |
| SharingType | string | Type of sharing permissions assigned to the target user |
| Site_ | string | GUID of the site where the file/folder is located |
| Site_Url | string | URL of the site where the file/folder is located |
| Source_Name | string | The entity that triggered the audited operation (`SharePoint` or `ObjectModel`) |
| SourceFileExtension | string | File extension of the file accessed by the user |
| SourceFileName | string | Name of the file or folder accessed by the user |
| SourceRecordId | string | Unique identifier of an audit record |
| SourceRelativeUrl | string | URL of the folder that contains the accessed file |
| SourceSystem | string | The type of agent the event was collected by |
| SRPolicyId | string | Policy ID |
| SRPolicyName | string | Policy name |
| SRRuleMatchDetails | dynamic | Rule details |
| Start_Time | datetime | The date and time at which the cmdlet was executed |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with |
| SupportTicketId | string | Customer support ticket ID for 'act-on-behalf-of' situations |
| TabType | string | The type of tab that generated this event |
| TargetContextId | string | GUID of the organization the targeted user belongs to |
| TargetUserId | string | Target user id |
| TargetUserOrGroupName | string | UPN or name of the target user/group a resource was shared with |
| TargetUserOrGroupType | string | Whether the target is a Member, Guest, Group, or Partner |
| TeamGuid | string | Unique identifier for the team being audited |
| TeamName | string | The name of the team being audited |
| TenantId | string | The Log Analytics workspace ID |
| TimeGenerated | datetime | UTC date/time when the user performed the activity |
| Type | string | The name of the table |
| UniqueSharingId | string | The unique sharing ID associated with the sharing operation |
| UserAgent | string | The user agent string of the client |
| UserDomain | string | The domain of the user |
| **UserId** | string | The **UPN of the user who performed the action** in `Operation` — the primary actor identity |
| UserKey | string | An alternative ID for the user identified in `UserId` |
| UserSharedWith | string | The user that a resource was shared with |
| UserType | string | The type of user that performed the operation (Regular, Admin, etc.; see UserType) |

> All ~150 reference columns are listed above. The acting identity is **`UserId`** (not `UserPrincipalName` — that column does not exist here).

## Key columns for detection & hunting
- **Identity:** `UserId` is the acting user's UPN (the one to pivot on). `Actor` / `LogonUserDisplayName` are friendly-name variants; `MailboxOwnerUPN` is the *owner* of a mailbox that was accessed (may differ from `UserId` on delegate access); `TargetUserId` / `AADTarget` / `TargetUserOrGroupName` are the *target* of an action.
- **Host / device:** No Windows hostname column. `ClientMachineName` (Outlook host), `DeviceInformation`, `Client` (browser/OS string), `IsManagedDevice` (bool).
- **Network:** `ClientIP` (SharePoint/general activity), `Client_IPAddress` (Exchange mailbox operations), and `ActorIpAddress` (Azure AD / SharePoint record types). A robust query coalesces all three.
- **Outcome / result:** `ResultStatus` — a **string** (e.g. `Succeeded`, `Failed`), not an int/bool. `ResultReasonType` and `LoginStatus` add detail.
- **Timestamps:** `TimeGenerated` (UTC, primary). Cmdlet-style records also carry `Start_Time`.
- **Join keys (to other tables):** `UserId` (UPN → `SigninLogs.UserPrincipalName`, `AuditLogs`, `IdentityInfo`), the IP columns (→ `SigninLogs.IPAddress`, `CommonSecurityLog`), `OfficeTenantId` / `OrganizationId` (tenant), `ClientMachineName` (→ device tables).

## ⚠️ Schema gotchas
- **`UserId`, not `UserPrincipalName`.** Sibling Entra tables use `UserPrincipalName`; OfficeActivity uses `UserId`. Joining on the wrong name silently returns nothing.
- **Three different IP columns by workload.** Exchange mailbox events populate `Client_IPAddress`; SharePoint/OneDrive populate `ClientIP`; Azure AD record types populate `ActorIpAddress`. Always `coalesce(ClientIP, Client_IPAddress, ActorIpAddress)`.
- **`ResultStatus` is a string.** Filter `== "Succeeded"` / `== "Failed"`, never a numeric comparison.
- **`Parameters` is a serialized string, not dynamic.** For cmdlet operations (e.g. `New-InboxRule`, `Set-Mailbox`) it holds a JSON-ish name/value array as **text** — `parse_json()` it before indexing. (`OperationProperties`, `AppAccessContext`, `Members` *are* true dynamic.)
- **`RecordType` and `OfficeWorkload` overlap but differ.** `OfficeWorkload` is the coarse service; `RecordType` (e.g. `ExchangeAdmin`, `SharePointSharingOperation`, `AzureActiveDirectoryStsLogon`) is the finer audit class. Filter on `Operation` for specific actions.
- **`OfficeObjectId` holds the full SharePoint/OneDrive URL** (only populated for those workloads) — it is the object identity, while `Site_Url` is just the site root.

## 🧪 Sample data
[`OfficeActivity_sample.csv`](OfficeActivity_sample.csv) — 26 rows. Compromised finance analyst **alexw** is driven from the attacker IP `185.220.101.2`: a malicious **New-InboxRule** that auto-forwards finance mail to an external domain and deletes it, a `Set-Mailbox` SMTP-forward for persistence, a burst of SharePoint/OneDrive **FileDownloaded** + anonymous-link/external-sharing exfil of finance documents, and mailbox clean-up (`HardDelete`); benign Teams/Exchange/SharePoint activity from meganb, jamest, and priya.menon is mixed in as noise, plus a legitimate `itadmin` role grant.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `OfficeWorkload`, `RecordType`, `Operation`, `UserId`, `UserType`, `ResultStatus`, `ClientIP`, `Client_IPAddress`, `ActorIpAddress`, `OfficeObjectId`, `SourceFileName`, `Site_Url`, `Parameters`, `ClientInfoString`, `UserAgent`. This is the **Microsoft 365 BEC + data-exfiltration** step of "Operation Quiet Ledger" — alexw's compromised session pivots from the risky sign-in (in `SigninLogs`) into mailbox persistence and SharePoint exfiltration.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Malicious inbox rule / mail forwarding (BEC persistence) — [T1114.003](https://attack.mitre.org/techniques/T1114/003/)
**Hypothesis:** A compromised mailbox creates an auto-forwarding/deleting inbox rule or sets external SMTP forwarding to exfiltrate mail.
```kusto
OfficeActivity
| where OfficeWorkload == "Exchange"
| where Operation in ("New-InboxRule", "Set-InboxRule", "UpdateInboxRules", "Set-Mailbox")
| extend Params = parse_json(Parameters)
| extend ActorIP = coalesce(ClientIP, Client_IPAddress, ActorIpAddress)
| where Parameters has_any ("ForwardTo", "ForwardingSmtpAddress", "RedirectTo", "DeleteMessage")
| project TimeGenerated, UserId, Operation, ActorIP, Parameters
| sort by TimeGenerated asc
```
**Triage:** True positive = forwarding to an external/look-alike domain from an unusual IP (here `185.220.101.2` → `login-contoso-sso.com` / `badupdate-cdn.com`). Benign = a user forwarding to a known internal assistant or a sanctioned domain.

### H2 · Mass file download / staging before exfil — [T1530](https://attack.mitre.org/techniques/T1530/)
**Hypothesis:** A single user downloads or full-syncs an abnormal volume of SharePoint/OneDrive files in a short window.
```kusto
OfficeActivity
| where OfficeWorkload in ("SharePoint", "OneDrive")
| where Operation in ("FileDownloaded", "FileSyncDownloadedFull")
| extend ActorIP = coalesce(ClientIP, Client_IPAddress, ActorIpAddress)
| summarize Files = count(), Names = make_set(SourceFileName, 20),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
          by UserId, ActorIP, bin(TimeGenerated, 1h)
| where Files >= 4
| sort by Files desc
```
**Triage:** True positive = a non-bulk user pulling many sensitive files from one foreign IP in minutes (alexw downloads 5 finance files from `185.220.101.2`). Benign = OneDrive client doing an expected first-time full sync from a corp IP.

### H3 · External / anonymous sharing of sensitive content — [T1567.002](https://attack.mitre.org/techniques/T1567/002/)
**Hypothesis:** Files are shared externally or via anonymous links, moving data outside the tenant.
```kusto
OfficeActivity
| where RecordType == "SharePointSharingOperation"
| where Operation in ("SharingSet", "AnonymousLinkCreated", "AddedToSecureLink", "SharingInvitationCreated")
| extend Params = parse_json(Parameters)
| extend SharedWith = tostring(Params[0].Value)
| extend ActorIP = coalesce(ClientIP, Client_IPAddress, ActorIpAddress)
| project TimeGenerated, UserId, Operation, SourceFileName, SharedWith, ActorIP
| sort by TimeGenerated asc
```
**Triage:** True positive = anonymous link or guest share of finance documents from a suspicious session. Benign = expected guest collaboration on a project site.

### H4 · Audit-log tampering / evidence destruction — [T1070.008](https://attack.mitre.org/techniques/T1070/008/)
**Hypothesis:** After exfiltration, the actor hard-deletes sent items or files to destroy evidence.
```kusto
OfficeActivity
| where Operation in ("HardDelete", "SoftDelete", "MoveToDeletedItems", "FileDeleted", "FileRecycled")
| extend ActorIP = coalesce(ClientIP, Client_IPAddress, ActorIpAddress)
| project TimeGenerated, UserId, OfficeWorkload, Operation, OfficeObjectId, ActorIP
| sort by TimeGenerated asc
```
**Triage:** True positive = deletes from the same compromised IP immediately after suspicious sends/downloads (alexw `HardDelete` of Sent Items + OneDrive `FileDeleted` from `185.220.101.2`). Benign = routine user housekeeping.

## 🔗 Correlates with
- **SigninLogs** on `UserId` ↔ `UserPrincipalName` (and IP columns ↔ `IPAddress`) — confirm the risky/foreign sign-in that preceded the mailbox and file activity.
- **AuditLogs** on `UserId` ↔ `InitiatedBy.user.userPrincipalName` — tie the `Add member to role` here to the Entra directory audit for the same privilege escalation.
- **IdentityInfo** on `UserId` ↔ `AccountUPN` — enrich the actor with department, manager, and risk context.
- **CloudAppEvents / McasShadowItReporting** on `UserId` — cross-check Defender for Cloud Apps for the same file-download/sharing session when MCAS is connected.

## 📚 References
- [OfficeActivity table reference — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/officeactivity)
- [OfficeActivity sample queries — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/officeactivity)
- [Detect and remediate the Outlook rules and forms attack — Microsoft Defender for Office 365](https://learn.microsoft.com/en-us/defender-office-365/detect-and-remediate-outlook-rules-forms-attack)
