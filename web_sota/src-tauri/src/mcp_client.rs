use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};

const SERVER_KEY: &str = "windows-computer-use-mcp";
const MCP_URL: &str = "http://127.0.0.1:10789/mcp";

fn cursor_config_path() -> Option<PathBuf> {
    std::env::var("USERPROFILE")
        .ok()
        .map(|home| PathBuf::from(home).join(".cursor").join("mcp.json"))
}

fn claude_config_path() -> Option<PathBuf> {
    std::env::var("APPDATA")
        .ok()
        .map(|appdata| {
            PathBuf::from(appdata)
                .join("Claude")
                .join("claude_desktop_config.json")
        })
}

fn read_config(path: &Path) -> serde_json::Value {
    match fs::read_to_string(path) {
        Ok(content) => serde_json::from_str(&content).unwrap_or_else(|_| serde_json::json!({})),
        Err(_) => serde_json::json!({}),
    }
}

fn write_config(path: &Path, value: &serde_json::Value) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("create config dir: {e}"))?;
    }
    let serialized =
        serde_json::to_string_pretty(value).map_err(|e| format!("serialize config: {e}"))?;
    fs::write(path, format!("{serialized}\n")).map_err(|e| format!("write config: {e}"))
}

fn is_registered_in_config(path: &Path) -> bool {
    let root = read_config(path);
    root.get("mcpServers")
        .and_then(|servers| servers.get(SERVER_KEY))
        .and_then(|entry| entry.get("url"))
        .and_then(|url| url.as_str())
        == Some(MCP_URL)
}

fn register_in_config(path: &Path) -> Result<(), String> {
    let mut root = read_config(path);
    let object = root
        .as_object_mut()
        .ok_or_else(|| "config root must be a JSON object".to_string())?;

    if !object.contains_key("mcpServers") {
        object.insert("mcpServers".into(), serde_json::json!({}));
    }

    let servers = object
        .get_mut("mcpServers")
        .and_then(|value| value.as_object_mut())
        .ok_or_else(|| "mcpServers must be a JSON object".to_string())?;

    servers.insert(
        SERVER_KEY.into(),
        serde_json::json!({ "url": MCP_URL }),
    );

    write_config(path, &root)
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct McpRegistrationStatus {
    pub mcp_url: String,
    pub cursor_registered: bool,
    pub claude_registered: bool,
    pub cursor_config_path: Option<String>,
    pub claude_config_path: Option<String>,
}

#[tauri::command]
pub fn get_mcp_registration_status() -> McpRegistrationStatus {
    let cursor_path = cursor_config_path();
    let claude_path = claude_config_path();

    McpRegistrationStatus {
        mcp_url: MCP_URL.into(),
        cursor_registered: cursor_path
            .as_ref()
            .map(|path| is_registered_in_config(path))
            .unwrap_or(false),
        claude_registered: claude_path
            .as_ref()
            .map(|path| is_registered_in_config(path))
            .unwrap_or(false),
        cursor_config_path: cursor_path.map(|path| path.display().to_string()),
        claude_config_path: claude_path.map(|path| path.display().to_string()),
    }
}

#[tauri::command]
pub fn register_mcp_clients(cursor: bool, claude: bool) -> Result<String, String> {
    let mut updated = Vec::new();
    let mut skipped = Vec::new();

    if cursor {
        match cursor_config_path() {
            Some(path) => {
                register_in_config(&path)?;
                updated.push("Cursor");
            }
            None => return Err("USERPROFILE is not set".into()),
        }
    } else {
        skipped.push("Cursor");
    }

    if claude {
        match claude_config_path() {
            Some(path) => {
                register_in_config(&path)?;
                updated.push("Claude Desktop");
            }
            None => return Err("APPDATA is not set".into()),
        }
    } else {
        skipped.push("Claude Desktop");
    }

    if updated.is_empty() {
        return Err("Select at least one MCP client".into());
    }

    let mut message = format!("Registered windows-computer-use-mcp in {}", updated.join(" and "));
    if !skipped.is_empty() {
        message.push_str(&format!(" (skipped {})", skipped.join(", ")));
    }
    Ok(message)
}
