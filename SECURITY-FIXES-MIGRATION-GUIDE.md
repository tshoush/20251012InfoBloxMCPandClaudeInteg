# Security Fixes Migration Guide

**Status:** Ready to Apply
**Estimated Time:** 2-3 hours
**Priority:** CRITICAL - Must complete before production use

---

## New Security Modules Created ✅

The following secure modules have been created and are ready to use:

1. **config.py** - Centralized configuration (no hardcoded credentials)
2. **logging_config.py** - Structured logging with security audit trail
3. **validators.py** - Input validation to prevent injection attacks
4. **.env.example** - Environment variable template

---

## Migration Steps

### Step 1: Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or vim, code, etc.

# Set these values:
INFOBLOX_HOST=your-actual-infoblox-host
INFOBLOX_USER=your-username
INFOBLOX_PASSWORD=your-password
ANTHROPIC_API_KEY=your-api-key
```

### Step 2: Update Python Files

Each Python file needs these changes:

#### A. Replace Hardcoded Config with New Module

**OLD CODE (Remove This):**
```python
# INSECURE - Remove these lines
INFOBLOX_HOST = os.getenv("INFOBLOX_HOST", "192.168.1.224")
INFOBLOX_USER = os.getenv("INFOBLOX_USER", "admin")
INFOBLOX_PASSWORD = os.getenv("INFOBLOX_PASSWORD", "infoblox")

# INSECURE - Remove SSL suppression
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
session.verify = False
```

**NEW CODE (Add This):**
```python
# Import secure configuration
from config import get_settings
from logging_config import setup_logging, get_security_logger, log_tool_execution
from validators import InputValidator, ValidationError

# Load configuration
settings = get_settings()

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    enable_security_audit=settings.enable_security_audit
)

logger = logging.getLogger(__name__)
security_logger = get_security_logger()

# Display SSL warning if disabled
settings.display_security_warning()

# Use configuration
INFOBLOX_HOST = settings.infoblox_host
BASE_URL = settings.get_infoblox_base_url()

# Configure session with proper SSL
session = requests.Session()
session.verify = settings.get_ssl_verify()
```

#### B. Add Input Validation

**In `process_tool_call` function:**

```python
def process_tool_call(tool_name: str, tool_input: dict):
    """Process tool calls with validation"""
    logger.info(f"Tool call: {tool_name}")

    try:
        # Validate inputs
        validated_input = InputValidator.validate_tool_input(tool_name, tool_input)

        # Execute tool
        if tool_name == "infoblox_query":
            result = infoblox_query(**validated_input)
            success = "error" not in result
            log_tool_execution(tool_name, validated_input, success)
            return result

        # ... other tools ...

    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return {"error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return {"error": "Tool execution failed"}
```

#### C. Replace Print Statements with Logging

**OLD:**
```python
print(f"Error: {e}")
print(f"Processing query...")
```

**NEW:**
```python
logger.error(f"Error: {e}", exc_info=True)
logger.info("Processing query...")
```

---

### Step 3: Test Configuration

```bash
# Test that configuration loads correctly
python3 config.py

# Expected output if env vars are set:
# ✓ Configuration loaded successfully
#   InfoBlox: your-host
#   WAPI Version: v2.13.1
#   SSL Verify: True

# Expected output if env vars missing:
# CONFIGURATION ERROR: Missing required environment variables
# [detailed error message]
```

### Step 4: Test Logging

```bash
# Test logging works
python3 logging_config.py

# Check logs created:
ls -lh ~/.ddi-assistant/logs/
# Should show:
#   ddi-assistant.log
#   security_audit.log
```

### Step 5: Test Validators

```bash
# Test validators work
python3 validators.py

# Expected output:
# Testing InputValidator...
# ✓ Correctly blocked SQL injection attempt
# ✓ Correctly blocked invalid network
# ✓ Correctly blocked command injection attempt
# ✓ All validation tests passed!
```

---

## Files to Update

### Priority 1: Main Application Files

1. **claude-chat-rag.py**
   - Import config, logging, validators
   - Remove hardcoded credentials (lines 39-42)
   - Remove SSL suppression (lines 34-36)
   - Add input validation in process_tool_call
   - Replace print with logger

2. **infoblox-mcp-server.py**
   - Same changes as above
   - Lines to update: 16-17, 24-27, 46

3. **infoblox-rag-builder.py**
   - Same changes as above
   - Lines to update: 29-32

4. **infoblox-explorer.py**
   - Same changes as above

### Priority 2: Shell Scripts

Update to check for environment variables:

```bash
# In setup scripts, add check:
if [ -z "$INFOBLOX_HOST" ]; then
    echo "Error: INFOBLOX_HOST not set"
    echo "Please set environment variables. See .env.example"
    exit 1
fi
```

---

## Quick Reference: Import Statements

Add these to the top of each Python file:

```python
#!/usr/bin/env python3
"""
[Your docstring here]
"""

import logging

# Import security modules
from config import get_settings, ConfigurationError
from logging_config import setup_logging, get_security_logger, log_tool_execution, log_security_event
from validators import InputValidator, ValidationError

# ... other imports ...

# Initialize at module level
try:
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file
    )
    logger = logging.getLogger(__name__)

    # Display warning if SSL disabled
    settings.display_security_warning()

except ConfigurationError as e:
    print(str(e))
    sys.exit(1)
```

---

## Testing Checklist

After making changes, test:

- [ ] Application starts without credentials in code
- [ ] Application fails gracefully if .env missing
- [ ] SSL verification enabled (or warning shown)
- [ ] Logs created in ~/.ddi-assistant/logs/
- [ ] Security audit log captures events
- [ ] Input validation blocks injection attempts
- [ ] All tools still function correctly

---

## Rollback Plan

If issues occur:

```bash
# Revert to previous version
git checkout HEAD -- claude-chat-rag.py

# Or keep backup:
cp claude-chat-rag.py claude-chat-rag.py.backup
```

---

## Next Steps

After security fixes are applied:

1. ✅ Test thoroughly
2. ✅ Commit changes
3. ✅ Proceed to unit testing
4. ✅ Update documentation

Would you like me to proceed with creating the test framework now?
