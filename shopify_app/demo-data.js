export const demoCatalog = [
  {
    category: "Drivers",
    products: [
      { title: "Metly Aero Driver 9.5", price: "3499.00", cost: "1800.00" },
      { title: "Metly Aero Driver 10.5", price: "3499.00", cost: "1800.00" },
      { title: "Metly Carbon Driver HL", price: "3799.00", cost: "1950.00" },
    ],
  },
  {
    category: "Fairway Woods",
    products: [
      { title: "Metly Fairway Wood 3", price: "2299.00", cost: "1180.00" },
      { title: "Metly Fairway Wood 5", price: "2199.00", cost: "1125.00" },
      { title: "Metly Hybrid Rescue 4", price: "1899.00", cost: "980.00" },
    ],
  },
  {
    category: "Irons",
    products: [
      { title: "Metly Forged Iron Set 4-PW", price: "6999.00", cost: "3600.00" },
      { title: "Metly Distance Iron Set 5-PW", price: "5799.00", cost: "2980.00" },
      { title: "Metly Players 7 Iron", price: "1099.00", cost: "540.00" },
    ],
  },
  {
    category: "Wedges",
    products: [
      { title: "Metly Spin Wedge 52", price: "1199.00", cost: "590.00" },
      { title: "Metly Spin Wedge 56", price: "1199.00", cost: "590.00" },
      { title: "Metly Spin Wedge 60", price: "1199.00", cost: "590.00" },
    ],
  },
  {
    category: "Putters",
    products: [
      { title: "Metly Blade Putter", price: "1799.00", cost: "880.00" },
      { title: "Metly Mallet Putter", price: "1899.00", cost: "930.00" },
      { title: "Metly Counterbalance Putter", price: "1999.00", cost: "980.00" },
    ],
  },
  {
    category: "Bags",
    products: [
      { title: "Metly Tour Cart Bag", price: "1999.00", cost: "950.00" },
      { title: "Metly Stand Bag Lite", price: "1599.00", cost: "760.00" },
      { title: "Metly Weekend Pencil Bag", price: "999.00", cost: "430.00" },
    ],
  },
  {
    category: "Balls",
    products: [
      { title: "Metly Tour Ball 12-Pack", price: "399.00", cost: "165.00" },
      { title: "Metly Soft Ball 12-Pack", price: "349.00", cost: "150.00" },
      { title: "Metly Distance Ball 24-Pack", price: "499.00", cost: "210.00" },
    ],
  },
  {
    category: "Gloves",
    products: [
      { title: "Metly Cabretta Glove Left M", price: "179.00", cost: "62.00" },
      { title: "Metly Cabretta Glove Left L", price: "179.00", cost: "62.00" },
      { title: "Metly All Weather Glove Pair", price: "249.00", cost: "90.00" },
    ],
  },
]

export const demoCustomers = [
  { firstName: "Mads", lastName: "Andersen", email: "mads.andersen.demo@metly.dk", city: "Aarhus" },
  { firstName: "Sofie", lastName: "Jensen", email: "sofie.jensen.demo@metly.dk", city: "København" },
  { firstName: "Emil", lastName: "Nielsen", email: "emil.nielsen.demo@metly.dk", city: "Odense" },
  { firstName: "Laura", lastName: "Hansen", email: "laura.hansen.demo@metly.dk", city: "Aalborg" },
  { firstName: "Magnus", lastName: "Pedersen", email: "magnus.pedersen.demo@metly.dk", city: "Esbjerg" },
  { firstName: "Freja", lastName: "Christensen", email: "freja.christensen.demo@metly.dk", city: "Randers" },
  { firstName: "Oliver", lastName: "Larsen", email: "oliver.larsen.demo@metly.dk", city: "Kolding" },
  { firstName: "Clara", lastName: "Madsen", email: "clara.madsen.demo@metly.dk", city: "Vejle" },
  { firstName: "Noah", lastName: "Kristensen", email: "noah.kristensen.demo@metly.dk", city: "Herning" },
  { firstName: "Ida", lastName: "Mortensen", email: "ida.mortensen.demo@metly.dk", city: "Silkeborg" },
]

export function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function pickRandom(items) {
  return items[randomInt(0, items.length - 1)]
}
