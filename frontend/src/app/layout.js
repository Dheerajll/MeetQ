import { Geist, Geist_Mono } from "next/font/google";
import { Space_Grotesk, Inter, IBM_Plex_Mono } from "next/font/google";
import Providers from "./providers";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

export const metadata = {
  title: "Meeting Agent",
  description: "Your AI meeting agent — capture, summarize, act.",
};

export default function RootLayout({ children }) {
  return (
     <html lang="en">
      <body className={`${spaceGrotesk.variable} ${inter.variable} ${plexMono.variable}`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
