"""
Génération de documents PDF à partir des templates HTML + Jinja2 + WeasyPrint.
Gère les factures, devis, attestations URSSAF, extraits Kbis et RIB.
"""

import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from config import TEMPLATES_DIR, TVA_RATES, TEAM_MEMBERS
from models import (
    Company, LineItem, Invoice, Devis,
    AttestationURSSAF, ExtraitKbis, RIB,
)

fake = Faker("fr_FR")

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

PRESTATIONS = [
    "Développement application web",
    "Maintenance serveur Linux",
    "Audit sécurité informatique",
    "Formation Python avancé",
    "Refonte interface utilisateur",
    "Intégration API REST",
    "Migration base de données",
    "Support technique mensuel",
    "Analyse de données marketing",
    "Création site e-commerce",
    "Consulting stratégie digitale",
    "Installation réseau fibre",
    "Réparation matériel informatique",
    "Licence logiciel annuelle",
    "Hébergement cloud dédié",
    "Prestation de nettoyage industriel",
    "Fourniture de matériel bureautique",
    "Transport de marchandises",
    "Travaux de peinture intérieure",
    "Entretien espaces verts",
]

BANQUES = [
    ("Crédit Agricole", "17106", "00045", "AGRIFRPP"),
    ("BNP Paribas", "30004", "01234", "BNPAFRPP"),
    ("Société Générale", "30003", "02847", "SOGEFRPP"),
    ("Crédit Mutuel", "10278", "06500", "CMCIFR2A"),
    ("La Banque Postale", "20041", "01005", "PSSTFRPP"),
    ("CIC", "30066", "10808", "CMCIFRPP"),
    ("Caisse d'Épargne", "11425", "00100", "CEPAFRPP"),
]


def _random_lines(min_items: int = 1, max_items: int = 6) -> list[LineItem]:
    n = random.randint(min_items, max_items)
    return [
        LineItem(
            description=random.choice(PRESTATIONS),
            quantite=random.randint(1, 20),
            prix_unitaire_ht=round(random.uniform(50, 5000), 2),
        )
        for _ in range(n)
    ]


def generate_invoice(emetteur: Company, client: Company, show_titre: bool = True) -> tuple[Invoice, str]:
    """Génère une facture légitime et retourne (Invoice, html_string). show_titre=False = sans intitulé FACTURE."""
    date_emission = fake.date_between(start_date="-6m", end_date="today")
    lignes = _random_lines()
    taux_tva = random.choice(TVA_RATES)

    invoice = Invoice(
        numero=f"FAC-{date_emission.year}-{random.randint(1000, 9999)}",
        date_emission=date_emission,
        date_echeance=date_emission + timedelta(days=random.choice([30, 45, 60])),
        emetteur=emetteur,
        client=client,
        lignes=lignes,
        taux_tva=taux_tva,
    )

    template = env.get_template("facture.html")
    html = template.render(
        emetteur=emetteur,
        client=client,
        numero=invoice.numero,
        date_emission=invoice.date_emission.strftime("%d/%m/%Y"),
        date_echeance=invoice.date_echeance.strftime("%d/%m/%Y"),
        lignes=lignes,
        taux_tva=invoice.taux_tva,
        total_ht=invoice.total_ht,
        montant_tva=invoice.montant_tva,
        total_ttc=invoice.total_ttc,
        show_titre=show_titre,
    )
    return invoice, html


def generate_devis(emetteur: Company, client: Company, show_titre: bool = True) -> tuple[Devis, str]:
    """Génère un devis légitime. show_titre=False = sans intitulé DEVIS."""
    date_emission = fake.date_between(start_date="-6m", end_date="today")
    lignes = _random_lines()
    taux_tva = random.choice(TVA_RATES)

    devis = Devis(
        numero=f"DEV-{date_emission.year}-{random.randint(1000, 9999)}",
        date_emission=date_emission,
        date_validite=date_emission + timedelta(days=random.choice([30, 60, 90])),
        emetteur=emetteur,
        client=client,
        lignes=lignes,
        taux_tva=taux_tva,
    )

    template = env.get_template("devis.html")
    html = template.render(
        emetteur=emetteur,
        client=client,
        numero=devis.numero,
        date_emission=devis.date_emission.strftime("%d/%m/%Y"),
        date_validite=devis.date_validite.strftime("%d/%m/%Y"),
        lignes=lignes,
        taux_tva=devis.taux_tva,
        total_ht=devis.total_ht,
        montant_tva=devis.montant_tva,
        total_ttc=devis.total_ttc,
        show_titre=show_titre,
    )
    return devis, html


def generate_attestation_urssaf(
    entreprise: Company, expired: bool = False
) -> tuple[AttestationURSSAF, str]:
    """Génère une attestation de vigilance URSSAF."""
    if expired:
        date_fin = fake.date_between(start_date="-2y", end_date="-1d")
        date_debut = date_fin - timedelta(days=180)
    else:
        date_debut = fake.date_between(start_date="-3m", end_date="today")
        date_fin = date_debut + timedelta(days=180)

    attestation = AttestationURSSAF(
        numero=f"ATT-URSSAF-{random.randint(100000, 999999)}",
        entreprise=entreprise,
        date_debut_validite=date_debut,
        date_fin_validite=date_fin,
        date_delivrance=date_debut - timedelta(days=random.randint(0, 10)),
        effectif_salarie=random.randint(1, 200),
        situation_compte="À jour" if not expired else random.choice(["À jour", "En anomalie"]),
    )

    template = env.get_template("attestation_urssaf.html")
    html = template.render(
        entreprise=entreprise,
        numero=attestation.numero,
        date_delivrance=attestation.date_delivrance.strftime("%d/%m/%Y"),
        date_debut_validite=attestation.date_debut_validite.strftime("%d/%m/%Y"),
        date_fin_validite=attestation.date_fin_validite.strftime("%d/%m/%Y"),
        effectif_salarie=attestation.effectif_salarie,
        situation_compte=attestation.situation_compte,
        expired=expired,
    )
    return attestation, html


def generate_kbis(entreprise: Company) -> tuple[ExtraitKbis, str]:
    """Génère un extrait Kbis."""
    date_immat = fake.date_between(start_date="-15y", end_date="-1y")

    kbis = ExtraitKbis(
        entreprise=entreprise,
        date_immatriculation=date_immat,
        date_extrait=fake.date_between(start_date="-3m", end_date="today"),
    )

    template = env.get_template("kbis.html")
    html = template.render(
        entreprise=entreprise,
        date_immatriculation=kbis.date_immatriculation.strftime("%d/%m/%Y"),
        date_extrait=kbis.date_extrait.strftime("%d/%m/%Y"),
        numero_rcs=kbis.numero_rcs,
        greffe=kbis.greffe,
        activite_principale=kbis.activite_principale,
    )
    return kbis, html


def generate_rib(entreprise: Company) -> tuple[RIB, str]:
    """Génère un RIB."""
    banque_info = random.choice(BANQUES)
    numero_compte = "".join([str(random.randint(0, 9)) for _ in range(11)])
    cle = str(random.randint(10, 99))
    iban_base = f"FR76{banque_info[1]}{banque_info[2]}{numero_compte}{cle}"
    iban_formatted = " ".join([iban_base[i:i+4] for i in range(0, len(iban_base), 4)])

    rib = RIB(
        entreprise=entreprise,
        banque=banque_info[0],
        code_banque=banque_info[1],
        code_guichet=banque_info[2],
        numero_compte=numero_compte,
        cle_rib=cle,
        iban=iban_formatted,
        bic=banque_info[3],
    )

    template = env.get_template("rib.html")
    html = template.render(
        entreprise=entreprise,
        banque=rib.banque,
        code_banque=rib.code_banque,
        code_guichet=rib.code_guichet,
        numero_compte=rib.numero_compte,
        cle_rib=rib.cle_rib,
        iban=rib.iban,
        bic=rib.bic,
    )
    return rib, html


def render_pdf(html_content: str, output_path: Path) -> None:
    """Convertit un HTML en PDF via xhtml2pdf."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output_path), "w+b") as f:
        status = pisa.CreatePDF(html_content, dest=f)
        if status.err:
            raise RuntimeError(f"Erreur xhtml2pdf: {status.err}")
