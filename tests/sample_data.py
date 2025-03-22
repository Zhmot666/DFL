"""
Sample data for testing JSON Schema Validator
These structures match the expected format as described in the README
"""

# Valid sample data with complete structure
VALID_JSON_DATA = {
    "pckagent": {
        "pckagentinfo": {
            "vunp": "123456789",
            "nmns": "001",
            "vexec": "Иванов И.И.",
            "vphn": "8029123456",
            "ngod": "2023",
            "ntype": "1",
            "dcreate": "2023-12-31"
        },
        "docagent": [
            {
                "docagentinfo": {
                    "cln": "4090773C014PB3",
                    "vfam": "Петров",
                    "vname": "Петр",
                    "votch": "Петрович"
                },
                "tar4": [
                    {
                        "nmonth": "1",
                        "summa": "1200.00"
                    },
                    {
                        "nmonth": "2",
                        "summa": "1300.00"
                    }
                ],
                "tar14": [
                    {
                        "nmonth": "1",
                        "summa": "120.00"
                    }
                ]
            },
            {
                "docagentinfo": {
                    "cln": "5090773C014PB4",
                    "vfam": "Сидоров",
                    "vname": "Иван",
                    "votch": "Сидорович"
                },
                "tar4": [
                    {
                        "nmonth": "1",
                        "summa": "2200.00"
                    },
                    {
                        "nmonth": "2",
                        "summa": "2300.00"
                    }
                ],
                "tar14": [
                    {
                        "nmonth": "1",
                        "summa": "220.00"
                    }
                ]
            }
        ]
    }
}

# Invalid JSON data missing required fields
INVALID_JSON_DATA = {
    "pckagent": {
        "pckagentinfo": {
            "vunp": "123456789",
            # Missing required fields
        },
        "docagent": [
            {
                "docagentinfo": {
                    "cln": "4090773C014PB3",
                    # Missing required fields
                },
                "tar4": [
                    {
                        # Missing nmonth
                        "summa": "1200.00"
                    }
                ]
            }
        ]
    }
}

# Sample JSON with duplicate CLN values
JSON_WITH_DUPLICATE_CLN = {
    "pckagent": {
        "pckagentinfo": {
            "vunp": "123456789",
            "nmns": "001",
            "vexec": "Иванов И.И.",
            "vphn": "8029123456",
            "ngod": "2023",
            "ntype": "1",
            "dcreate": "2023-12-31"
        },
        "docagent": [
            {
                "docagentinfo": {
                    "cln": "4090773C014PB3",
                    "vfam": "Петров",
                    "vname": "Петр",
                    "votch": "Петрович"
                }
            },
            {
                "docagentinfo": {
                    "cln": "4090773C014PB3",  # Duplicate CLN
                    "vfam": "Сидоров",
                    "vname": "Иван",
                    "votch": "Сидорович"
                }
            }
        ]
    }
}

# Sample for testing tar14/tar4 synchronization
JSON_FOR_TAR_SYNC = {
    "pckagent": {
        "pckagentinfo": {
            "vunp": "123456789",
            "nmns": "001",
            "vexec": "Иванов И.И.",
            "vphn": "8029123456",
            "ngod": "2023",
            "ntype": "1",
            "dcreate": "2023-12-31"
        },
        "docagent": [
            {
                "docagentinfo": {
                    "cln": "4090773C014PB3",
                    "vfam": "Петров",
                    "vname": "Петр",
                    "votch": "Петрович"
                },
                "tar4": [
                    {"nmonth": "1", "summa": "1000.00"},
                    {"nmonth": "2", "summa": "1100.00"},
                    {"nmonth": "3", "summa": "1200.00"}
                ],
                "tar14": [
                    {"nmonth": "1", "summa": "100.00"}
                    # Missing entries for months 2 and 3
                ]
            }
        ]
    }
}

# Sample JSON schema matching the structure
SAMPLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "title": "Schema for validation",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "pckagent": {
            "type": "object",
            "additionalProperties": False,
            "required": ["pckagentinfo", "docagent"],
            "properties": {
                "pckagentinfo": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["vunp", "nmns", "vexec", "vphn", "ngod", "ntype", "dcreate"],
                    "properties": {
                        "vunp": {"type": "string"},
                        "nmns": {"type": "string"},
                        "vexec": {"type": "string"},
                        "vphn": {"type": "string"},
                        "ngod": {"type": "string"},
                        "ntype": {"type": "string"},
                        "dcreate": {"type": "string"}
                    }
                },
                "docagent": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["docagentinfo"],
                        "properties": {
                            "docagentinfo": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["cln", "vfam", "vname", "votch"],
                                "properties": {
                                    "cln": {"type": "string"},
                                    "vfam": {"type": "string"},
                                    "vname": {"type": "string"},
                                    "votch": {"type": "string"}
                                }
                            },
                            "tar4": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["nmonth", "summa"],
                                    "properties": {
                                        "nmonth": {"type": "string"},
                                        "summa": {"type": "string"}
                                    }
                                }
                            },
                            "tar14": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["nmonth", "summa"],
                                    "properties": {
                                        "nmonth": {"type": "string"},
                                        "summa": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
} 