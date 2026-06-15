# windows-computer-use-mcp — Safety & isolation

**Read this before enabling this server in an IDE.** Desktop automation is **host-powerful**; “sandbox safety” for **untrusted UI** requires a **second fleet server**, not pywinauto alone.

**Foreground / focus:** If you automate “start app X and test it,” read **[OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md)** — the user should **step back from the terminal/IDE** so automation does not fight for focus.

---

## Dual-use tooling: research, forensics, and guardrails

### Why this looks “malware-adjacent”

Anything that does **session-wide capture**, **low-level hooks**, or **unattended control of the desktop** shares **capabilities** with a lot of offensive tooling. That is an observation about **surface area**, not a moral verdict on this repository.

### Why hosted assistants sometimes refuse to help

A model vendor may decline to **generate** keyloggers or similar hooks because they optimize for **reducing harm from misuse**. That policy stance is about **mass-market generation**, not a technical claim that your use case is wrong.

### Legitimate uses

The same mechanisms support **bug reproduction**, **test harnesses**, **workflow instrumentation**, and **forensics or research on machines you own or are explicitly authorized to assess**. Capability overlaps with malware; **intent and authorization** do not.

### What this repo does about it

Optional, high-risk features (for example **`global_keylogger`** — see **§6**) are **off by default**, gated by **environment opt-in**, **human-in-the-loop** where applicable, **kill switch** / **dry-run**, and this document—because **failure modes** (misconfigured MCP server, lost laptop, accidental exposure) are serious, not because ethical security work is suspect.

### Capability vs. intent

**“Malware-adjacent” in capability** is fair; **“malware” in intent** is **not** implied. Use this project only under **law, policy, and consent** appropriate to your environment.

---

## 1. Two-server model (recommended for new users)

| Goal | Install |
|------|---------|
| **Drive the real Windows desktop** (your session) | **windows-computer-use-mcp** (this repo) + **`approve_automation`**, env limits below |
| **Disposable desktop** (Windows Sandbox / VM) for installs + UI tests | **Also install `virtualization-mcp`** (fleet repo) — launches Sandbox, maps `assets`, optional dev stack / AIRGAP |

**windows-computer-use-mcp does not spin up Windows Sandbox.** For **full** isolation, add **virtualization-mcp** to your MCP client and use it to **provision** the box; run **automation inside the guest** (script with pywinauto) or a test runner — see fleet doc below.

---

## 2. Built into this server (host session)

- **HITL (human-in-the-loop):** `approve_automation` — required for mutating **mouse** / **keyboard** (except `automation_mouse("position")` and `automation_mouse("telemetry")`).
- **Env:** `WINDOWS_COMPUTER_USE_MCP_KILL_SWITCH`, `WINDOWS_COMPUTER_USE_MCP_MAX_ACTIONS_PER_MINUTE`, `WINDOWS_COMPUTER_USE_MCP_DRY_RUN`.
- **HITL (human-in-the-loop) bypass:** `WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1` allows zero-friction automation in trusted demo environments (disables security prompts).
- **Pointer injection:** Mutating **mouse** paths use **`win32_mouse`** (`SetCursorPos` / `mouse_event`, DPI-aware), not PyAutoGUI alone. **Failsafe:** moving the cursor to the **upper-left screen corner** aborts injected pointer ops (same idea as PyAutoGUI). **`WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1`** disables both **`pyautogui.FAILSAFE`** and that **`win32_mouse`** corner check for trusted demos/CI.
- **Tool:** `automation_safety(status | reset_counters)`.
- **Telemetry HUD:** The `automation_mouse("telemetry")` operation provides visible, on-screen verification of inputs. It is **non-persistent** and **localized** (volatile memory only), ensuring auditing without the security risks of background logging.

---

## 3. Fleet documentation (canonical)

Clone **mcp-central-docs** (sibling repo) and read:

- **`patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md`** — sampling amplification, IDE chain rules, **sandboxed execution** (guest-side pywinauto + virtualization-mcp).
- **`patterns/FLEET_COMPUTER_USE_MCP.md`** — computer-use architecture, mitigations.

---

## 4. Do not

- Put **windows-computer-use-mcp** in the **default IDE chain** for **web-only** work — use a **browser MCP** (typically **Playwright**-based) for Vite/webapps and **HTML DOM** / network / console analysis. **pywinauto** targets **native Windows UI**, not the browser’s DOM; keep the split explicit.
- Rely on **host** pywinauto to “click inside” the Windows Sandbox window — automate **inside** the guest session instead.
- Treat **OpenManus** + **openmanus-mcp** + **pywinauto** + **OpenClaw / Manus-class** autonomy as **low-friction** — that combination **multiplies** tool loops and sampling against **OS-wide** input. See **mcp-central-docs** `patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md` § *OpenManus, openmanus-mcp, OpenClaw, Manus-class* and **integrations/openmanus.md** (Caution block).

---

## 5. Face recognition (`automation_face`) — opt-in, implemented, not default

**Not a roadmap-only idea** — the tool is **implemented** but **excluded from default installs** (no `face` extra, env flag unset). It is for **local, operator-initiated** webcam capture on a machine you control — not ambient surveillance.

The **`automation_face`** tool is **off by default**. Two steps are required to expose it:

1. **Operator opt-in (runtime):** set **`WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1`** (or `true` / `yes` / `on`) in the server environment (see **`automation_safety(status)`** — `face_tool_opt_in` / `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE`).
2. **Dependencies:** install the **`face`** extra (see `pyproject.toml`) so the face-recognition stack is available.

Without both, the server does **not** register **`automation_face`**; other portmanteau tools are unchanged.

### Why it exists

It supports **explicit, local** workflows for **operator presence** at the machine: e.g. a coarse “is the intended person still at this PC?” signal to **reduce casual misuse** if someone else sits down at an unlocked session while **desktop automation** is in play. That is **not** strong authentication, not a compliance control, and not a substitute for locking the screen — but it can **raise the bar** together with **HITL (human-in-the-loop)**, **env limits**, and normal session hygiene.

### Communication

Describe it as **optional**, **consent-based**, **local**, and **for operator presence** — not for covert or remote monitoring. Demos and README should state that clearly.

### Treat face data as sensitive

- Stored encodings and images under **`data/known_faces/`** (or paths your deployment uses) are **biometric-adjacent** — protect them like **secrets** (disk encryption, backups policy, who can read the repo).
- **Do not** imply that face match **prevents** misuse; it only **narrows** risk when integrated thoughtfully.

### If you do not need it

Leave **`WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE`** unset (default). Do not install the **`face`** extra. Window/element automation does not require face features.

### Camera hardware (`capture`)

**Supported:** Any camera that Windows exposes to **OpenCV** via `cv2.VideoCapture(index)` — typically:

- **Integrated / built-in** laptop camera (often listed as *Integrated Camera* in Device Manager).
- **Standard USB webcams** (UVC / “USB Video Device” class).

Use the **`camera_index`** argument (`0`, `1`, …) to pick the device. Order is **OS enumeration order**, not a fixed name: the built-in cam is often **`0`** when it is the default; an external USB cam may be **`0`** or **`1`** depending on what Windows assigns. There is **no** special product name “usbcam” in the API — that is just informal shorthand some people use for **USB UVC** webcams.

**Out of scope (for now):** **TP-Link Tapo**, other **IP / RTSP / cloud** cameras, and stacks that need vendor apps or RTSP URLs. Those are unnecessarily complicated for local **`capture`**; use a **built-in or USB UVC** camera instead.

---

## 6. Global keyboard capture (`global_keylogger`) — opt-in, high-risk, non-stealth

This project is **not** a hacker or spyware tool. **`global_keylogger`** exists only as an **explicit, operator-controlled** debugging aid — never enabled in default installs, never silent background exfiltration.

The **`global_keylogger`** tool is **off by default**. The server does **not** register it unless you set:

- **`WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1`** (or `true` / `yes` / `on`) in the server environment.

See **`automation_safety(status)`** — `keylogger_tool_opt_in` / `WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER`.

### Why it exists

Session-wide keyboard hooks support **authorized** debugging and analysis (for example reproducing focus/shortcut issues, or **instrumenting** a session under explicit policy). This is **dual-use**: the same API surface is sensitive if misused.

### How it is gated

- **Opt-in** at registration time (env above).
- **`approve_automation`** / **HITL (human-in-the-loop)** applies to **`start`** the same way as other sensitive input tools (unless **`WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL`** is set — see §2).
- **`WINDOWS_COMPUTER_USE_MCP_KILL_SWITCH=1`** blocks starting capture; **`WINDOWS_COMPUTER_USE_MCP_DRY_RUN=1`** simulates **`start`** without installing the hook.
- The MCP server attempts to **stop** the listener on shutdown.
- Events live in a **bounded in-memory ring buffer** exposed only via MCP `read` — not written to hidden log files.
- **`start`** requires **HITL approval** (same as other sensitive input) unless bypass is explicitly set.

### If you do not need it

Leave **`WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER`** unset. Window, element, mouse, and normal keyboard **simulation** do not require it.
