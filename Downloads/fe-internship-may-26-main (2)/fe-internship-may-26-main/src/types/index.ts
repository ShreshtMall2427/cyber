export type Category = 'Framework' | 'Library' | 'Tool' | 'Language'

export interface Item {
  id: number
  name: string
  category: Category
  description: string
  stars: number
}
