// Brand assets reused from the original basadot WordPress site so the new pages
// match its look. These live on the same domain (served by WordPress at root),
// so absolute URLs work from the /crm app with no CORS/next-image config.
// If the site is ever fully migrated off WordPress, re-host these and update here.
export const BRAND = {
  logo: "https://sadot.lavit.io/wp-content/uploads/2022/05/לוגו-בשדות-5-300x300.png",
  heroAdopt: "https://sadot.lavit.io/wp-content/uploads/2022/10/17.jpg",
  name: "פנסיון בשדות",
} as const;
