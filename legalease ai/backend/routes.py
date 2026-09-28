from fastapi import (
    APIRouter,
    HTTPException,
)
from fastapi.responses import Response

from backend.ai_core.gemini_generator import (
    GeminiDocumentGenerator,
)
from backend.config import get_settings
from backend.schemas import (
    DocumentRequest,
    DocumentResponse,
    ExportRequest,
    HealthResponse,
)
from backend.services.document_exporter import (
    format_docx,
    format_pdf,
    format_txt,
)
from backend.services.text_utils import (
    safe_filename,
)


router = APIRouter()

settings = get_settings()

generator = GeminiDocumentGenerator(
    settings
)


# =================================================
# HEALTH
# =================================================

@router.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:

    if settings.mock_ai:

        ai_mode = "mock"

    elif settings.gemini_api_key:

        ai_mode = "gemini"

    else:

        ai_mode = "unconfigured"

    return HealthResponse(
        status="ok",
        ai_mode=ai_mode,
        model=settings.gemini_model,
    )


# =================================================
# GENERATE DOCUMENT
# =================================================

@router.post(
    "/generate",
    response_model=DocumentResponse,
)
def generate_document(
    request: DocumentRequest,
) -> DocumentResponse:

    try:

        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date.isoformat(),
        )

        return DocumentResponse(
            document_type=request.document_type,
            content=content,
            model=(
                "mock"
                if settings.mock_ai
                else settings.gemini_model
            ),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Document generation failed. "
                "Check the API configuration "
                "and try again."
            ),
        ) from exc


# =================================================
# EXPORT DOCUMENT
# =================================================

@router.post(
    "/export/{file_format}"
)
def export_document(
    file_format: str,
    request: ExportRequest,
):

    fmt = file_format.lower().strip()

    # ---------------------------------------------
    # TXT
    # ---------------------------------------------

    if fmt == "txt":

        payload = format_txt(
            request.content
        )

        media_type = (
            "text/plain; charset=utf-8"
        )

    # ---------------------------------------------
    # DOCX
    # ---------------------------------------------

    elif fmt == "docx":

        payload = format_docx(
            request.content,
            request.document_type,
        )

        media_type = (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    # ---------------------------------------------
    # PDF
    # ---------------------------------------------

    elif fmt == "pdf":

        payload = format_pdf(
            request.content,
            request.document_type,
        )

        media_type = (
            "application/pdf"
        )

    # ---------------------------------------------
    # INVALID FORMAT
    # ---------------------------------------------

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported format. "
                "Use txt, docx, or pdf."
            ),
        )

    filename = safe_filename(
        request.document_type,
        fmt,
    )

    return Response(
        content=payload,
        media_type=media_type,
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )