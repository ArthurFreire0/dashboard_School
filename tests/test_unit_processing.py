import numpy as np
from dashboard_school.processing import (
    remove_accents,
    normalize_str,
    map_admission_type,
    map_enrollment_status,
    map_discipline_status,
    map_payment_status
)


class TestRemoveAccents:
    def test_remove_accents_with_portuguese_chars(self):
        assert remove_accents("café") == "cafe"
        assert remove_accents("açúcar") == "acucar"
        assert remove_accents("protón") == "proton"

    def test_remove_accents_with_no_accents(self):
        assert remove_accents("hello") == "hello"
        assert remove_accents("test123") == "test123"


class TestNormalizeStr:
    def test_normalize_str_basic(self):
        assert normalize_str("Hello World") == "hello_world"
        assert normalize_str("Test-Case") == "test_case"

    def test_normalize_str_with_accents(self):
        assert normalize_str("Formação") == "formacao"
        assert normalize_str("Período Letivo") == "periodo_letivo"

    def test_normalize_str_with_tabs_and_spaces(self):
        assert normalize_str("test\ttabs") == "test_tabs"
        assert normalize_str("  multiple   spaces  ") == "multiple_spaces"


class TestMapAdmissionType:
    def test_map_admission_type_transfer_external(self):
        assert map_admission_type("transferencia_externa") == "transferencia_externa"
        assert map_admission_type("EXTERNAL TRANSFER") == "transferencia_externa"
        assert map_admission_type("Transferência Externa") == "transferencia_externa"

    def test_map_admission_type_transfer_internal(self):
        assert map_admission_type("transferencia_interna") == "transferencia_interna"
        assert map_admission_type("internal transfer") == "transferencia_interna"

    def test_map_admission_type_entrance_exam(self):
        assert map_admission_type("vestibular") == "vestibular"
        assert map_admission_type("entrance exam") == "vestibular"

    def test_map_admission_type_default(self):
        assert map_admission_type(np.nan) == "vestibular"
        assert map_admission_type("unknown") == "vestibular"
        assert map_admission_type("") == "vestibular"


class TestMapEnrollmentStatus:
    def test_map_enrollment_status_active(self):
        assert map_enrollment_status("ativo") == "ativo"
        assert map_enrollment_status("ACTIVE") == "ativo"
        assert map_enrollment_status("matriculado") == "ativo"

    def test_map_enrollment_status_dropped(self):
        assert map_enrollment_status("evadido") == "evadido"
        assert map_enrollment_status("dropped") == "evadido"
        assert map_enrollment_status("desistente") == "evadido"

    def test_map_enrollment_status_suspended(self):
        assert map_enrollment_status("trancado") == "trancado"
        assert map_enrollment_status("suspended") == "trancado"
        assert map_enrollment_status("trancamento") == "trancado"

    def test_map_enrollment_status_default(self):
        assert map_enrollment_status(np.nan) == "ativo"
        assert map_enrollment_status("unknown") == "ativo"


class TestMapDisciplineStatus:
    def test_map_discipline_status_approved(self):
        assert map_discipline_status("aprovado") == "aprovado"
        assert map_discipline_status("APPROVED") == "aprovado"
        assert map_discipline_status("passed") == "aprovado"

    def test_map_discipline_status_failed(self):
        assert map_discipline_status("reprovado") == "reprovado"
        assert map_discipline_status("failed") == "reprovado"
        assert map_discipline_status("reprovação") == "reprovado"


class TestMapPaymentStatus:
    def test_map_payment_status_paid(self):
        assert map_payment_status("pago") == "pago"
        assert map_payment_status("PAID") == "pago"
        assert map_payment_status("quitado") == "pago"

    def test_map_payment_status_overdue(self):
        assert map_payment_status("atrasado") == "atrasado"
        assert map_payment_status("overdue") == "atrasado"
        assert map_payment_status("late") == "atrasado"
        assert map_payment_status("vencido") == "atrasado"