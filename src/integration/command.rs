use std::path::Path;

#[cfg(any(windows, test))]
use base64::Engine;

pub(crate) fn shell_single_quote(value: &str) -> String {
    format!("'{}'", value.replace('\'', "'\"'\"'"))
}

pub(crate) fn hook_command(hook_path: &Path, action: Option<&str>) -> String {
    let path = hook_path.display().to_string();
    #[cfg(windows)]
    {
        let mut command = format!(
            "powershell -NoProfile -ExecutionPolicy Bypass -File {}",
            windows_command_quote(&path)
        );
        if let Some(action) = action {
            command.push(' ');
            command.push_str(action);
        }
        command
    }

    #[cfg(not(windows))]
    {
        let mut command = format!("bash {}", shell_single_quote(&path));
        if let Some(action) = action {
            command.push(' ');
            command.push_str(action);
        }
        command
    }
}

#[cfg(any(windows, test))]
pub(crate) fn powershell_encoded_hook_command(hook_path: &Path, action: &str) -> String {
    let path = hook_path.display().to_string().replace('\'', "''");
    let script = format!("& '{path}' {action}");
    let encoded_script = script
        .encode_utf16()
        .flat_map(u16::to_le_bytes)
        .collect::<Vec<_>>();
    let encoded = base64::engine::general_purpose::STANDARD.encode(encoded_script);
    format!("powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded}")
}

pub(crate) fn legacy_bash_hook_command(hook_path: &Path, action: Option<&str>) -> String {
    let mut command = format!(
        "bash {}",
        shell_single_quote(&hook_path.display().to_string())
    );
    if let Some(action) = action {
        command.push(' ');
        command.push_str(action);
    }
    command
}

/// The unquoted `bash <path> <action>` spelling of [`legacy_bash_hook_command`].
/// Bash runs it identically only when the path needs no quoting, so paths with
/// any other character yield `None` instead of a command that runs differently.
pub(crate) fn unquoted_bash_hook_command(
    hook_path: &Path,
    action: Option<&str>,
) -> Option<String> {
    let path = hook_path.display().to_string();
    if path.is_empty() || !path.chars().all(is_shell_safe_path_char) {
        return None;
    }
    let mut command = format!("bash {path}");
    if let Some(action) = action {
        command.push(' ');
        command.push_str(action);
    }
    Some(command)
}

fn is_shell_safe_path_char(ch: char) -> bool {
    ch.is_ascii_alphanumeric() || matches!(ch, '/' | '.' | '_' | '-' | '+' | ',')
}

#[cfg(windows)]
fn windows_command_quote(value: &str) -> String {
    format!("\"{}\"", value.replace('"', "\\\""))
}
