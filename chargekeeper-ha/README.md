# ChargeKeeper pour Home Assistant

Intégration personnalisée (HACS) qui remonte dans Home Assistant l'état de vos bornes
supervisées sur **ChargeKeeper** (API REST `https://rest.service-evse.com/v1`).

## Installation via HACS

1. HACS → ⋮ → **Dépôts personnalisés** → collez l'URL de votre dépôt GitHub, catégorie **Intégration**.
2. Installez **ChargeKeeper**, puis redémarrez Home Assistant.
3. **Paramètres → Appareils et services → Ajouter une intégration → ChargeKeeper**.
4. Saisissez **email**, **mot de passe** et **tenant**, puis (optionnel) l'**ID de la borne**
   tel qu'affiché dans ChargeKeeper. Laissez vide pour récupérer toutes les bornes du compte ;
   plusieurs IDs possibles, séparés par des virgules.

## Entités

Pour chaque borne (appareil) :

| Entité | Détail |
|---|---|
| En ligne | connectivité de la borne avec la supervision |
| Dernière communication, Firmware | diagnostic |
| Version OCPP, Puissance maximale | diagnostic (désactivés par défaut) |

Pour chaque connecteur :

| Entité | Détail |
|---|---|
| État | Disponible, Préparation, En charge, Suspendu…, En défaut |
| En charge | binaire |
| Puissance | W |
| Énergie de la session | Wh (affichée en kWh), compatible tableau de bord Énergie |
| Niveau batterie | % (si remonté par le véhicule) |
| Code d'erreur | diagnostic |
| Inactivité, Transaction | diagnostic (désactivés par défaut) |

## Options

Intervalle de mise à jour (30 s par défaut, minimum 10 s) : **Configurer** sur l'intégration.

## Dépannage

- **Email, mot de passe ou tenant invalide** : vérifiez les trois champs (la connexion se fait
  via `POST /v1/auth/signin`).
- Activez les logs : `logger: logs: custom_components.chargekeeper: debug`.
