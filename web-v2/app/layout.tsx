import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter"
});

const display = Space_Grotesk({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
  weight: ["400", "500", "600", "700"]
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
  weight: ["400", "500"]
});

export const metadata: Metadata = {
  metadataBase: new URL("https://cerealrisk.app"),
  title: {
    default: "CerealRisk · Climate-food risk intelligence",
    template: "%s · CerealRisk"
  },
  description:
    "An interactive geospatial platform exploring how ENSO and MJO climate signals shape agricultural exposure across global cereal systems.",
  applicationName: "CerealRisk",
  authors: [{ name: "Paola Andrea Ruiz Franco" }],
  keywords: [
    "ENSO",
    "MJO",
    "cereal yield",
    "climate risk",
    "agricultural insurance",
    "parametric triggers",
    "Pacific SST",
    "SOM",
    "GEOGLAM"
  ],
  openGraph: {
    title: "CerealRisk",
    description: "Climate-food risk intelligence for global cereal systems.",
    type: "website",
    siteName: "CerealRisk",
    images: [
      {
        url: "/cerealrisk-icon.jpg",
        width: 1024,
        height: 1024,
        alt: "CerealRisk climate and cereal icon"
      }
    ]
  },
  icons: {
    icon: [{ url: "/cerealrisk-icon.jpg", type: "image/jpeg" }],
    shortcut: [{ url: "/cerealrisk-icon.jpg", type: "image/jpeg" }],
    apple: [{ url: "/cerealrisk-icon.jpg", type: "image/jpeg" }]
  },
  robots: {
    index: true,
    follow: true
  }
};

export const viewport: Viewport = {
  themeColor: "#050B12",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${display.variable} ${mono.variable}`}>
      <body className="min-h-screen bg-bg-deep text-ink antialiased">
        <Header />
        <main className="relative">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
