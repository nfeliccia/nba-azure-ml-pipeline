# AZ-900 Networking Cheat Sheet
## Private Endpoint vs Service Endpoint vs VPN Gateway vs ExpressRoute

### 1) Private Endpoint (Azure Private Link)
**What it is**
- A **private IP** in your VNet that maps to a specific Azure PaaS resource (e.g., Azure SQL, Storage).

**Key idea**
- “My PaaS service is reachable like it’s inside my network.”
- Enables **private connectivity to PaaS** without using public internet.

**Security posture**
- Best for “no public exposure” designs.
- Often paired with **Public network access: Disabled** on the service.

**DNS note**
- Usually needs **Private DNS** (`privatelink.*`) so the normal service hostname resolves to the private IP inside the VNet.

**When to use**
- You want PaaS access over private IP and strong isolation.

---

### 2) Service Endpoint (VNet Service Endpoints)
**What it is**
- Extends your VNet identity to Azure services so traffic from that subnet to the service is treated as coming from the VNet.

**Key idea**
- Traffic still goes to the service’s **public endpoint**, but it travels over the Azure backbone and the service can restrict access to specific VNets/subnets.

**Security posture**
- Reduces exposure by limiting which VNets can access the service, but the service endpoint is still “public addressable.”
- Not the same as “private IP in my subnet.”

**DNS note**
- Typically no special DNS required (still uses public service FQDN).

**When to use**
- You want VNet-based restriction but don’t need a private IP mapping (or the service doesn’t support Private Link in your scenario).

---

### 3) VPN Gateway (Point-to-Site / Site-to-Site)
**What it is**
- A managed Azure gateway that terminates VPN tunnels into a VNet.

**Point-to-Site (P2S)**
- Individual client (laptop) connects into Azure.
- Client usually gets an IP from a **VPN address pool** (often RFC1918 like 10.x/172.x).

**Site-to-Site (S2S)**
- Connects an on-prem network (or another cloud network) to Azure via IPSec tunnel.

**Key idea**
- “Remote user/site becomes part of the network (routing-wise).”
- Lets you reach **private IPs** in Azure (VNets, private endpoints, private VMs).

**Security posture**
- Strong when combined with good auth, least privilege, monitoring, and segmentation.
- Exposes a **public IP on the VPN gateway** (that’s how the tunnel is reached), but data is encrypted.

**When to use**
- You need secure connectivity from outside Azure into a private VNet.

---

### 4) ExpressRoute
**What it is**
- A **private circuit** from on-prem (or colocation) to Microsoft’s network (not over public internet).
- Uses BGP and enterprise routing patterns.

**Key idea**
- “A dedicated private link into Azure.”
- More consistent latency and reliability than VPN over internet.

**Security posture**
- Very strong (private connectivity), typically used by enterprises.
- Still needs good identity + segmentation controls.

**When to use**
- Large-scale, business-critical hybrid connectivity.

---

## Fast compare (exam-style)
- **Private Endpoint**: private IP in your VNet to reach PaaS (Private Link). Best isolation.
- **Service Endpoint**: secure path + subnet restriction to a PaaS public endpoint. Not a private IP mapping.
- **VPN Gateway**: encrypted tunnel over the internet into your VNet (P2S for users, S2S for networks).
- **ExpressRoute**: private circuit into Microsoft network (enterprise-grade hybrid).

---

## Common “gotchas”
- Private Endpoint usually needs **Private DNS** so the service name resolves privately inside the VNet.
- Service Endpoint != Private Endpoint:
  - Service endpoint still uses the service’s public address.
  - Private endpoint gives a private IP in your VNet.
- VPN/ExpressRoute are about **bringing a client/network into the private address space** so private resources are reachable.
