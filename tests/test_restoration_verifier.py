from restoration.verifier import (
    RestorationVerifier,
)


def test_matching_files_are_verified(
    tmp_path,
):

    source = tmp_path / "source.bin"
    restored = tmp_path / "restored.bin"

    source.write_bytes(
        b"DIGI ARTIFACT GUARD"
    )

    restored.write_bytes(
        b"DIGI ARTIFACT GUARD"
    )

    verifier = RestorationVerifier()

    result = verifier.verify(
        source,
        restored,
    )

    assert result.verified is True
    assert result.status == "VERIFIED"

    assert (
        result.source_hash
        == result.restored_hash
    )


def test_modified_file_is_detected(
    tmp_path,
):

    source = tmp_path / "source.bin"
    restored = tmp_path / "restored.bin"

    source.write_bytes(
        b"ORIGINAL"
    )

    restored.write_bytes(
        b"MODIFIED"
    )

    verifier = RestorationVerifier()

    result = verifier.verify(
        source,
        restored,
    )

    assert result.verified is False
    assert result.status == "CORRUPTED"

    assert (
        result.source_hash
        != result.restored_hash
    )


def test_missing_source(
    tmp_path,
):

    restored = tmp_path / "restored.bin"

    restored.write_bytes(
        b"DATA"
    )

    verifier = RestorationVerifier()

    result = verifier.verify(
        tmp_path / "missing.bin",
        restored,
    )

    assert result.status == "FAILED"


def test_missing_restored_file(
    tmp_path,
):

    source = tmp_path / "source.bin"

    source.write_bytes(
        b"DATA"
    )

    verifier = RestorationVerifier()

    result = verifier.verify(
        source,
        tmp_path / "missing.bin",
    )

    assert result.status == "FAILED"
    