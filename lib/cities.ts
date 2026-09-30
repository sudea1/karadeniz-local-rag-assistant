export type City = {
  id: string
  name: string
  image: string
  spot: string
  tagline: string
}

export const cities: City[] = [
  {
    id: "trabzon",
    name: "Trabzon",
    image: "/cities/trabzon.png",
    spot: "Uzungöl",
    tagline: "Sisli göller ve bulut denizinin şehri",
  },
  {
    id: "rize",
    name: "Rize",
    image: "/cities/rize.png",
    spot: "Ayder & Fırtına Deresi",
    tagline: "Çay bahçeleri ve yeşilin binbir tonu",
  },
  {
    id: "artvin",
    name: "Artvin",
    image: "/cities/artvin.png",
    spot: "Pokut & Mençuna",
    tagline: "Bulutların üstündeki yaylalar",
  },
  {
    id: "giresun",
    name: "Giresun",
    image: "/cities/giresun.png",
    spot: "Giresun Adası",
    tagline: "Fındığın ve efsanelerin diyarı",
  },
  {
    id: "ordu",
    name: "Ordu",
    image: "/cities/ordu.png",
    spot: "Boztepe",
    tagline: "Teleferikle çıkılan manzara şöleni",
  },
  {
    id: "samsun",
    name: "Samsun",
    image: "/cities/samsun.png",
    spot: "Bandırma & Kızılırmak Deltası",
    tagline: "Kuşların ve tarihin buluştuğu sahil",
  },
  {
    id: "sinop",
    name: "Sinop",
    image: "/cities/sinop.png",
    spot: "Hamsilos Koyu",
    tagline: "Türkiye'nin en kuzeyindeki huzur",
  },
]
