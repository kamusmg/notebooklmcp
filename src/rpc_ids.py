"""RPC IDs for Google NotebookLM batchexecute endpoint (reverse-engineered).

If any RPC ID stops working, capture a new fixture and compare with the old one
to find the renamed ID in the batchexecute payload.
"""


class RpcId:
    CREATE_NOTEBOOK = "CCqFvf"
    ADD_SOURCE = "izAoDd"
    START_FAST_RESEARCH = "Ljjv0c"
    START_DEEP_RESEARCH = "QA9ei"
    POLL_RESEARCH = "e3bVqc"
    IMPORT_RESEARCH_SOURCES = "LBwxtb"
    GET_NOTEBOOK = "rLM1Ne"
    CREATE_ARTIFACT = "R7cb6c"
    LIST_ARTIFACTS = "gArtLc"
    QUERY = "GenerateFreeFormStreamed"  # Different endpoint, not batchexecute
