from __future__ import annotations


class HarnessError(RuntimeError):
    exit_code = 5
    status = "ERROR"


class ConfigurationError(HarnessError):
    exit_code = 2
    status = "ERROR"


class BlockedError(HarnessError):
    exit_code = 3
    status = "BLOCKED"


class AssertionFailure(HarnessError):
    exit_code = 4
    status = "FAIL"


class SafetyError(BlockedError):
    pass


class AbortedError(HarnessError):
    exit_code = 130
    status = "ABORTED"
