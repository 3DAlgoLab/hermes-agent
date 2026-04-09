# Cross-Platform Session Sharing

## Overview
This feature enables conversation history sharing across CLI, Telegram, and other platforms when a consistent `user_id` is used.

## How It Works

### 1. User ID Configuration

The `user_id` can be set in three ways (priority order):

1. **CLI argument**: `hermes chat --user-id jaeyoon`
2. **Environment variable**: `export HERMES_USER_ID=jaeyoon`
3. **Config file**: Add `user_id: jaeyoon` to `config.yaml`

### 2. Session Linking

When a session is created:
- The system looks up all sessions with the same `user_id` across platforms
- The most recent session with conversation history is selected
- That history is copied to the new session

### 3. Platform Integration

**CLI Mode:**
```bash
hermes chat --user-id jaeyoon
```

**Gateway Mode:**
Platform adapters (Telegram, Discord, etc.) should populate `user_id` in `SessionSource`:
```python
source = SessionSource(
    platform=Platform.TELEGRAM,
    chat_id=str(chat_id),
    user_id=str(user_id),  # ← User's Telegram ID
    user_name=user_name,
)
```

## Implementation Details

### Files Modified

1. **cli.py**
   - Added `user_id` parameter to `HermesCLI.__init__()`
   - Resolves user_id from CLI arg > env var > config
   - Passes user_id to AIAgent

2. **hermes_cli/main.py**
   - Added `--user-id` argument to chat parser
   - Passes user_id through to cli_main()

3. **gateway/session.py**
   - `_seed_cross_platform_session()`: Seeds new sessions with history from linked platforms
   - `_find_user_sessions()`: Queries SQLite DB for user's sessions across platforms

## Usage Examples

### Example 1: CLI with user_id
```bash
# Set user_id via environment variable
export HERMES_USER_ID=jaeyoon
hermes chat

# Or use CLI argument
hermes chat --user-id jaeyoon
```

### Example 2: Telegram Integration
When setting up Telegram, ensure the adapter passes user_id:
```python
# In gateway/platforms/telegram.py
source = SessionSource(
    platform=Platform.TELEGRAM,
    chat_id=str(update.effective_chat.id),
    user_id=str(update.effective_user.id),  # ← User's Telegram ID
    user_name=update.effective_user.name,
)
```

### Example 3: Config File
```yaml
# ~/.hermes/config.yaml
user_id: jaeyoon
model:
  default: anthropic/claude-sonnet-4
```

## Testing

To test cross-platform session sharing:

1. Start CLI with user_id:
   ```bash
   hermes chat --user-id testuser
   # Have a conversation...
   ```

2. In gateway mode (Telegram), send a message from the same user_id

3. The new session should be seeded with the CLI conversation history

## Notes

- User ID should be consistent across platforms for the same person
- Different people should have different user_ids
- If no user_id is set, sessions remain platform-isolated
- The feature is backward compatible - existing setups continue to work
