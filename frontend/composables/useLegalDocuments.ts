export type LegalDocumentKey = 'privacy' | 'dpa' | 'security'

export interface LegalDocumentSection {
  title: string
  body: string
}

export interface LegalDocumentContent {
  title: string
  subtitle: string
  sections: LegalDocumentSection[]
}

export const legalDocuments: Record<LegalDocumentKey, LegalDocumentContent> = {
  privacy: {
    title: 'Privatlivspolitik',
    subtitle: 'Hvordan Metly behandler webshopdata og personoplysninger.',
    sections: [
      {
        title: 'Hvilke data vi behandler',
        body: 'Metly behandler ordre-, produkt- og kundedata fra den webshop, du forbinder, for at levere prognoser, kundeindsigter og anbefalinger.',
      },
      {
        title: 'Dataminimering',
        body: 'Vi begrænser behandlingen til de felter, der er nødvendige for produktet. For Shopify gemmer vi som udgangspunkt ikke kundens navn, e-mail eller gadeadresse, når de ikke er nødvendige.',
      },
      {
        title: 'Formål',
        body: 'Data bruges kun til at levere Metlys analyse- og forecastfunktioner til den merchant, der har forbundet sin butik.',
      },
      {
        title: 'Opbevaring',
        body: 'Direkte kundeidentifikatorer pseudonymiseres automatisk efter en retentionperiode, og merchants kan bede om sletning af konto- og kundedata.',
      },
    ],
  },
  dpa: {
    title: 'Databehandlerbetingelser',
    subtitle: 'Rollefordeling mellem merchant og Metly.',
    sections: [
      {
        title: 'Rollefordeling',
        body: 'Merchanten er dataansvarlig for kundedata i webshoppen. Metly er databehandler og behandler kun data for at levere analyse, forecasting og forretningsindsigter.',
      },
      {
        title: 'Instruks og formål',
        body: 'Metly må kun behandle data til de formål, der er nødvendige for dashboards, prognoser, kundeanalyser og anbefalinger. Data bruges ikke til annoncering eller videresalg.',
      },
      {
        title: 'Ophør og sletning',
        body: 'Hvis samarbejdet ophører, eller hvis Shopify-onboarding fejler under signup, slettes brugerens konto og relaterede data i systemet.',
      },
    ],
  },
  security: {
    title: 'Sikkerhedsbeskrivelse',
    subtitle: 'Tekniske og organisatoriske sikkerhedsforanstaltninger.',
    sections: [
      {
        title: 'Kryptering i transit',
        body: 'Metly anvender HTTPS/TLS til kommunikation mellem browser, frontend, backend og eksterne integrationskilder.',
      },
      {
        title: 'Adgangsbegrænsning',
        body: 'Data er adskilt per merchant via bruger-id, og systemet returnerer kun data for den autentificerede bruger.',
      },
      {
        title: 'Retention',
        body: 'Backend-jobbet håndhæver retentionregler, så direkte kundeidentifikatorer ikke opbevares længere end nødvendigt.',
      },
      {
        title: 'Automatiserede anbefalinger',
        body: 'Metly leverer beslutningsstøtte og træffer ikke automatiske beslutninger med juridiske eller tilsvarende væsentlige virkninger for kunders rettigheder.',
      },
    ],
  },
}
