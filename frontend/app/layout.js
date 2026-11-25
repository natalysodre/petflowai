import { Baloo_2, Nunito } from "next/font/google";
import "./globals.css";

const titulo = Baloo_2({ subsets: ["latin"], weight: ["600", "800"], variable: "--fonte-titulo" });
const corpo = Nunito({ subsets: ["latin"], weight: ["400", "600", "700"], variable: "--fonte-corpo" });

export const metadata = {
  title: "PetFlow 🐾 Fale com a clínica",
  description: "Envie sua mensagem para a clínica veterinária PetFlow",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR" className={`${titulo.variable} ${corpo.variable}`}>
      <body>{children}</body>
    </html>
  );
}
