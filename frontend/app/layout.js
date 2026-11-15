import "./globals.css";

export const metadata = {
  title: "Fetva Arşivi — RAG Arama Prototipi",
  description:
    "Bir arama yöntemi seçin, sorunuzu yazın; arşiv size en ilgili fetvaları getirsin.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="najma-bg" aria-hidden="true"></div>
        {children}
      </body>
    </html>
  );
}
