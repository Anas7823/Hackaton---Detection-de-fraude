from dataclasses import dataclass, field
from datetime import date


@dataclass
class Company:
    siren: str
    siret: str
    nom: str
    adresse: str
    code_postal: str
    ville: str
    naf: str
    forme_juridique: str
    date_creation: str
    dirigeant: str
    capital_social: int = 10000
    tva_intra: str = ""

    def __post_init__(self):
        if not self.tva_intra:
            self.tva_intra = f"FR{''.join(self.siren[:2])}{self.siren}"


@dataclass
class LineItem:
    description: str
    quantite: int
    prix_unitaire_ht: float

    @property
    def total_ht(self) -> float:
        return round(self.quantite * self.prix_unitaire_ht, 2)


@dataclass
class Invoice:
    numero: str
    date_emission: date
    date_echeance: date
    emetteur: Company
    client: Company
    lignes: list[LineItem] = field(default_factory=list)
    taux_tva: float = 0.20

    @property
    def total_ht(self) -> float:
        return round(sum(l.total_ht for l in self.lignes), 2)

    @property
    def montant_tva(self) -> float:
        return round(self.total_ht * self.taux_tva, 2)

    @property
    def total_ttc(self) -> float:
        return round(self.total_ht + self.montant_tva, 2)


@dataclass
class Devis:
    numero: str
    date_emission: date
    date_validite: date
    emetteur: Company
    client: Company
    lignes: list[LineItem] = field(default_factory=list)
    taux_tva: float = 0.20

    @property
    def total_ht(self) -> float:
        return round(sum(l.total_ht for l in self.lignes), 2)

    @property
    def montant_tva(self) -> float:
        return round(self.total_ht * self.taux_tva, 2)

    @property
    def total_ttc(self) -> float:
        return round(self.total_ht + self.montant_tva, 2)


@dataclass
class AttestationURSSAF:
    numero: str
    entreprise: Company
    date_debut_validite: date
    date_fin_validite: date
    date_delivrance: date
    effectif_salarie: int = 5
    situation_compte: str = "À jour"


@dataclass
class ExtraitKbis:
    entreprise: Company
    date_immatriculation: date
    date_extrait: date
    numero_rcs: str = ""
    greffe: str = "Greffe du Tribunal de Commerce de Paris"
    activite_principale: str = "Conseil en systèmes et logiciels informatiques"

    def __post_init__(self):
        if not self.numero_rcs:
            self.numero_rcs = f"{self.entreprise.siren} RCS Paris"


@dataclass
class RIB:
    entreprise: Company
    banque: str
    code_banque: str
    code_guichet: str
    numero_compte: str
    cle_rib: str
    iban: str
    bic: str


@dataclass
class DocumentRecord:
    filename: str
    doc_type: str
    company_siret: str
    company_name: str
