import io
import zipfile
import pytest
from fastapi import HTTPException
from app.services.zip_analyzer import analyze_zip


# --------------------------------------------------
# HELPER: CREATE ZIP IN MEMORY
# --------------------------------------------------

def create_test_zip(files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(
                filename,
                content
            )
    return zip_buffer.getvalue()


# --------------------------------------------------
# TEST 1: VALID ZIP
# --------------------------------------------------

def test_valid_zip():
    zip_content = create_test_zip({
        "project/hello.py":
            'print("Hello World")'
    })
    result = analyze_zip(zip_content)
    assert result["files_analyzed"] == 1
    assert (
        "project/hello.py"
        in result["file_tree"]
    )
    assert (
        "project/hello.py"
        in result["source_files"]
    )


# --------------------------------------------------
# TEST 2: INVALID ZIP
# --------------------------------------------------

def test_invalid_zip():
    invalid_content = (
        b"This is not a ZIP file"
    )
    with pytest.raises(
        HTTPException
    ) as error:
        analyze_zip(
            invalid_content
        )
    assert (
        error.value.status_code
        == 400
    )


# --------------------------------------------------
# TEST 3: EMPTY ZIP
# --------------------------------------------------

def test_empty_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer,
        "w"
    ):
        pass
    with pytest.raises(
        HTTPException
    ) as error:
        analyze_zip(
            zip_buffer.getvalue()
        )
    assert (
        error.value.status_code
        == 400
    )


# --------------------------------------------------
# TEST 4: PATH TRAVERSAL ATTACK
# --------------------------------------------------

def test_unsafe_zip_path():
    zip_content = create_test_zip({
        "../dangerous.py":
            'print("Danger")'
    })
    with pytest.raises(
        HTTPException
    ) as error:
        analyze_zip(
            zip_content
        )
    assert (
        error.value.status_code
        == 400
    )
    assert (
        "Unsafe file path"
        in error.value.detail
    )


# --------------------------------------------------
# TEST 5: UNSUPPORTED FILES
# --------------------------------------------------

def test_unsupported_files():
    zip_content = create_test_zip({
        "project/image.exe":
            "Unsupported content"
    })
    with pytest.raises(
        HTTPException
    ) as error:
        analyze_zip(
            zip_content
        )
    assert (
        error.value.status_code
        == 400
    )
    assert (
        "No supported source files"
        in error.value.detail
    )


# --------------------------------------------------
# TEST 6: OVERSIZED FILE
# --------------------------------------------------

def test_oversized_file():
    large_content = (
        "A" * (2 * 1024 * 1024 + 1)
    )
    zip_content = create_test_zip({
        "project/large.py":
            large_content
    })
    with pytest.raises(
        HTTPException
    ) as error:
        analyze_zip(
            zip_content
        )
    assert (
        error.value.status_code
        == 400
    )
    assert (
        "maximum allowed size"
        in error.value.detail
    )
