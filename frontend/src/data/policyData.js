/**
 * Mock policy data for all insurance domains.
 * Keyed by category slug — used by PolicyResultsPage.
 */

const LOGO_1 = 'https://lh3.googleusercontent.com/aida/ADBb0uiFiQdpoBLghCxd3O-J20BKJdHlm6oaDtjEizWCnDjEtjk8TxoBDw8aOgpetNsNDr0g--3m-RJd6wYY7-CGVYopdAVtHivyx47XgtNaPLZfEfLNdJarSgSUG3ImGJYRLbuG0Bb53WGfzTU49pN-zUgCIUt8RC-H9oJ0cbppxotTdkkaNfuOI2iI17MGr_qQwst7EU3pBTgigytyNEYeTHO2_j-GT12c2RcF34BLJJNpjhx9nrU7Lh-MWb4LWzPwCfHJhxPZt1DwfQ';
const LOGO_2 = 'https://lh3.googleusercontent.com/aida/ADBb0ug7O15aHW6zNvbG92bonIqx5312WYTISx_ljWR7ekE2-H9tzqDSP0uUtIyTdOyp-hVpYYHGEEoJXF6YyG8WgtO6aQeD6_Qlklzu1sb4yIidSN0Umq5wIAFIP_nqlNT1eZXKbO73UjoF0KtuK0BXD1h9cC4tQT8g2HZkAxRlq5AXg-9AIqT5dBNGt2JEecZzQG2KElMWd9tmtIao79ClsSUR3wOPBBP2pt0_h-GDJ_FP_qhe2dtPpn6k2IKVFZseGbKhEUiJNclOuQ';
const LOGO_3 = 'https://lh3.googleusercontent.com/aida/ADBb0uioYvpV3fjcZMM0FqyuCh26zKbZQ-Hei1GOJgRgwZ_43NIkMm4BQmZCDDXzCAJ5QLcCJTq4nYAxsZ-NStovhp4bjPwylv_NQwxue1DYxVrWTqrSAYjIjDnuX3_emt9zOkzDy-CvQbr5LG84LIXBheVqKtFN5M5R41b7Ne5yEuGNaYw_XCryYNAnfYrx3FnLT1gD5v5_Fyi2ihP5Llpgp3afiYMyTfc8lnWEemui0cUV-SK-1UoSh44tIaXhGP4mBj3uNqaIs1FFW58';

export const POLICY_CATEGORIES = {
  health: {
    label: 'Health Insurance',
    subtitle: 'Comparing 42 policies from top-rated insurers in India',
    icon: 'health_and_safety',
    filters: [
      { id: 'age', label: 'Primary Member Age', type: 'select',
        options: ['18 - 30 Years', '31 - 45 Years', '46 - 60 Years', '60+ Years'], default: '31 - 45 Years' },
      { id: 'cashless', label: 'Cashless Facilities', type: 'checkbox', default: true },
      { id: 'nearby', label: 'Within 10km', type: 'checkbox', default: false },
    ],
    chips: [
      { label: 'Maternity Cover', active: true },
      { label: 'No-Claim Bonus', active: false },
      { label: 'OPD Cover', active: false },
      { label: 'Cashless', active: true },
    ],
    policies: [
      {
        id: 'h1', name: 'Optima Secure', logo: LOGO_1, badge: 'Most Popular',
        rating: '4.8', reviews: '2.4k',
        features: ['Cashless Hospitalization', 'Maternity Cover (₹1L)', 'No-Claim Bonus 100%', '9,500+ Hospitals'],
        highlight: 'Secure Benefit: Instantly doubles your base sum insured from day 1.',
        originalPrice: '₹18,450', price: '₹15,200', saving: 'Save ₹3,250',
      },
      {
        id: 'h2', name: 'Health Shield', logo: LOGO_2, badge: null,
        rating: '4.5', reviews: '1.1k',
        features: ['Cashless Hospitalization', 'Day Care Treatments', 'Post-Hospitalization'],
        missingFeatures: ['Maternity Cover'],
        highlight: '0% Co-payment across all ages for any hospital network.',
        price: '₹12,800', note: 'Tax Benefits included',
      },
      {
        id: 'h3', name: 'Global Care', logo: LOGO_3, badge: null,
        rating: '4.9', reviews: '480',
        features: ['International Coverage', 'Critical Illness Cover', 'Air Ambulance Support', 'Annual Health Checkup'],
        highlight: 'Personal Concierge for all hospital admissions & claims.',
        price: '₹28,600', note: 'Global Access Platinum',
        highlightVariant: 'premium',
      },
    ],
  },

  motor: {
    label: 'Motor Insurance',
    subtitle: '24 Matching policies found for your Honda City Petrol',
    icon: 'directions_car',
    vehicleInfo: { label: 'Your Car Value (IDV)', value: '₹8,45,000' },
    filters: [
      { id: 'vehicleAge', label: 'Vehicle Age', type: 'select',
        options: ['Brand New', '1-3 Years', '3-5 Years', '5+ Years'], default: '1-3 Years' },
      { id: 'petrol', label: 'Petrol', type: 'checkbox', default: true },
      { id: 'diesel', label: 'Diesel', type: 'checkbox', default: false },
      { id: 'electric', label: 'Electric', type: 'checkbox', default: false },
      { id: 'cng', label: 'CNG', type: 'checkbox', default: false },
    ],
    featuredPolicies: [
      {
        id: 'm1', logo: LOGO_3, badge: 'BEST VALUE', badgeVariant: 'secondary',
        price: '₹12,450',
        features: ['IDV: ₹8,15,000', 'Zero-Depreciation Included', 'Roadside Assistance (24/7)'],
      },
      {
        id: 'm2', logo: LOGO_1, badge: 'RECOMMENDED', badgeVariant: 'primary',
        price: '₹13,890',
        features: ['IDV: ₹8,45,000', 'Zero-Dep + Engine Protector', 'Cashless Garage Network: 5400+'],
      },
    ],
    listPolicies: [
      {
        id: 'm3', logo: LOGO_2, idv: '₹7,90,000', claimsSettled: '98.5%',
        keyFeatures: 'Roadside, Legal, No-Claim Bonus', premium: '₹11,200',
      },
      {
        id: 'm4', logoText: 'LITERA INS.', idv: '₹8,10,000', claimsSettled: '96.2%',
        keyFeatures: 'Zero-Dep, Key Replacement', premium: '₹12,800',
      },
    ],
  },

  agriculture: {
    label: 'Agriculture Insurance',
    subtitle: 'Protecting the backbone of the nation — Kharif season policies',
    icon: 'agriculture',
    filters: [
      { id: 'cropType', label: 'Crop Type', type: 'chips',
        options: ['Kharif', 'Rabi', 'Commercial'], default: 'Kharif' },
    ],
    policies: [
      {
        id: 'a1', name: 'PM Fasal Bima Yojana', logo: LOGO_1, badge: 'Government Backed',
        rating: '4.7', reviews: '12k',
        features: ['Crop Loss Coverage', 'Natural Calamity Protection', 'Post-Harvest Losses', 'Prevented Sowing'],
        highlight: 'Subsidised premium — farmers pay only 2% for Kharif crops.',
        price: '₹2,400', note: 'Per hectare / season',
      },
      {
        id: 'a2', name: 'Livestock Shield', logo: LOGO_2, badge: null,
        rating: '4.3', reviews: '3.2k',
        features: ['Cattle & Buffalo Cover', 'Accidental Death', 'Disease Cover', 'Veterinary Expenses'],
        highlight: 'Covers up to 10 animals per policy with no waiting period.',
        price: '₹3,800', note: 'Per animal / year',
      },
      {
        id: 'a3', name: 'Tractor & Equipment', logo: LOGO_3, badge: null,
        rating: '4.5', reviews: '1.8k',
        features: ['Own Damage Cover', 'Third-Party Liability', 'Fire & Theft', 'Breakdown Assistance'],
        highlight: 'Covers tractors, harvesters, and all farm machinery.',
        price: '₹8,200', note: 'Per vehicle / year',
      },
    ],
  },

  property: {
    label: 'Property Insurance',
    subtitle: 'Protect your home and business assets',
    icon: 'home_work',
    filters: [
      { id: 'propertyType', label: 'Property Type', type: 'select',
        options: ['Residential', 'Commercial', 'Industrial'], default: 'Residential' },
    ],
    policies: [
      {
        id: 'p1', name: 'Home Shield Pro', logo: LOGO_1, badge: 'Best Seller',
        rating: '4.6', reviews: '5.1k',
        features: ['Structure Coverage', 'Contents Cover', 'Fire & Flood', 'Burglary Protection'],
        highlight: '48-hour claim settlement SLA with dedicated home manager.',
        price: '₹8,500', note: 'Per year',
      },
      {
        id: 'p2', name: 'Shop Owners Policy', logo: LOGO_2, badge: null,
        rating: '4.4', reviews: '2.3k',
        features: ['Stock Coverage', 'Business Interruption', 'Public Liability', 'Electronic Equipment'],
        highlight: 'Covers up to ₹50L of stock with no sub-limits.',
        price: '₹12,000', note: 'Per year',
      },
    ],
  },
};

export const CATEGORY_SLUGS = Object.keys(POLICY_CATEGORIES);
