use hbb_common::{
    config::{LocalConfig, HARD_SETTINGS},
    sha2::{Digest, Sha256},
    sodiumoxide::utils::memcmp,
};

pub const OPTION_TK_NAMESPACE: &str = "tk-namespace";
const HARD_OPTION_TK_NS_HASH: &str = "tk-ns-hash";

pub fn local_namespace() -> String {
    LocalConfig::get_option(OPTION_TK_NAMESPACE)
}

pub fn is_namespace_allowed(tk_ns: &str) -> bool {
    let hard = HARD_SETTINGS
        .read()
        .unwrap()
        .get(HARD_OPTION_TK_NS_HASH)
        .cloned()
        .unwrap_or_default();
    if hard.trim().is_empty() {
        namespace_matches(option_env!("TK_NS_HASH").unwrap_or_default(), tk_ns)
    } else {
        namespace_matches(&hard, tk_ns)
    }
}

// An unset list disables the check; a set list with no valid entry rejects everyone,
// so a malformed hash never silently opens the device.
fn namespace_matches(hash_list: &str, tk_ns: &str) -> bool {
    if hash_list.trim().is_empty() {
        return true;
    }
    if tk_ns.is_empty() {
        return false;
    }
    let digest = Sha256::digest(tk_ns.as_bytes());
    let mut allowed = false;
    for expected in hash_list.split(',').filter_map(|s| decode_hex32(s.trim())) {
        allowed |= memcmp(digest.as_slice(), &expected);
    }
    allowed
}

fn decode_hex32(s: &str) -> Option<[u8; 32]> {
    let bytes = s.as_bytes();
    if bytes.len() != 64 {
        return None;
    }
    let mut out = [0u8; 32];
    for (i, pair) in bytes.chunks(2).enumerate() {
        let hi = (pair[0] as char).to_digit(16)?;
        let lo = (pair[1] as char).to_digit(16)?;
        out[i] = (hi * 16 + lo) as u8;
    }
    Some(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    // sha256("abc")
    const ABC: &str = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";

    #[test]
    fn unset_list_allows_everyone() {
        assert!(namespace_matches("", ""));
        assert!(namespace_matches(" ", "anything"));
    }

    #[test]
    fn matching_token_is_allowed() {
        assert!(namespace_matches(ABC, "abc"));
        assert!(namespace_matches(&ABC.to_uppercase(), "abc"));
        assert!(namespace_matches(&format!("{}, {}", "00".repeat(32), ABC), "abc"));
    }

    #[test]
    fn wrong_missing_or_malformed_is_rejected() {
        assert!(!namespace_matches(ABC, "abd"));
        assert!(!namespace_matches(ABC, ""));
        assert!(!namespace_matches("not-a-hash", "abc"));
    }
}
