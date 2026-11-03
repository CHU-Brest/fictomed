import pytest

from fictomed.sites.aphp.prompt import make_user_prompt


def _prompt(**values):
    return make_user_prompt(values, frozenset(), {})


def test_run11_clinical_columns_are_included_when_present():
    result = _prompt(
        age=55,
        sexe=1,
        taille_cm=169,
        poids_kg=77,
        imc=27.0,
        tabac="sevré depuis 28 ans (3 PA)",
        alcool="environ 12 verres/jour",
    )

    assert "- Taille : 169 cm\n" in result
    assert "- Poids : 77 kg (IMC 27,0)\n" in result
    assert "- Tabac : sevré depuis 28 ans (3 PA)\n" in result
    assert "- Alcool : environ 12 verres/jour\n" in result


def test_optional_clinical_columns_are_omitted_when_missing_or_null():
    result = _prompt(
        age=55,
        sexe=2,
        taille_cm=None,
        poids_kg=None,
        imc=float("nan"),
        tabac="",
        alcool=None,
    )

    assert "Taille" not in result
    assert "Poids" not in result
    assert "IMC" not in result
    assert "Tabac" not in result
    assert "Alcool" not in result


def test_imc_is_kept_when_weight_is_missing():
    result = _prompt(imc=21.25)

    assert "- IMC : 21,2\n" in result


def test_supported_aliases_are_formatted():
    result = _prompt(
        height_cm=170.5,
        weight_kg=70.2,
        bmi=24.3,
        tobacco_status="non",
        alcohol_status="occasionnel",
    )

    assert "- Taille : 170,5 cm\n" in result
    assert "- Poids : 70,2 kg (IMC 24,3)\n" in result
    assert "- Tabac : non\n" in result
    assert "- Alcool : occasionnel\n" in result


@pytest.mark.parametrize("technical_weight", [25.0, 0.5])
def test_sampling_weight_is_not_used_as_patient_weight(technical_weight):
    result = _prompt(poids=technical_weight)

    assert "Poids" not in result
