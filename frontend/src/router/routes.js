import MainLayout from 'layouts/MainLayout.vue'
import LandingPage from 'pages/LandingPage.vue'
import AboutLayout from 'pages/AboutLayout.vue'
import MissionLayout from 'pages/MissionLayout.vue'
import ProductsLayout from 'pages/ProductsLayout.vue'
import HeaderPanel from 'pages/HeaderPanel.vue'
import EarningsReleasesCard from 'components/cards/EarningsReleasesCard.vue'
import ErrorNotFound from 'pages/ErrorNotFound.vue'

// 1) Ensure your IndexPage is in /pages/:
//   src/pages/IndexPage.vue
//   We'll load it with a lazy import below

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', component: LandingPage },
      { path: 'about', component: AboutLayout },
      { path: 'mission', component: MissionLayout },
      { path: 'products', component: ProductsLayout },
      { path: 'header-test', component: HeaderPanel },
      { path: 'earnings-test', component: EarningsReleasesCard },

      // 2) Add your new route here:
      { path: 'dashboard', component: () => import('pages/IndexPage.vue') }
    ]
  },

  {
    path: '/:catchAll(.*)*',
    component: ErrorNotFound
  }
]

export default routes
