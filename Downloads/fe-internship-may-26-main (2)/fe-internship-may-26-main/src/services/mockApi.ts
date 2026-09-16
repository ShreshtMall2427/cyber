import type { Item } from '../types'

const ITEMS: Item[] = [
  { id: 1,  name: 'React',        category: 'Library',   description: 'A JavaScript library for building user interfaces with a declarative, component-based approach.',              stars: 224 },
  { id: 2,  name: 'Vue.js',       category: 'Framework', description: 'A progressive framework for building UIs, designed to be incrementally adoptable.',                             stars: 207 },
  { id: 3,  name: 'Angular',      category: 'Framework', description: 'A platform for building mobile and desktop web apps using TypeScript and a rich component model.',               stars: 95  },
  { id: 4,  name: 'Svelte',       category: 'Framework', description: 'A compiler that shifts work to build time, producing minimal vanilla JS with no virtual DOM overhead.',          stars: 79  },
  { id: 5,  name: 'Next.js',      category: 'Framework', description: 'The React framework for production -- hybrid static and server rendering, file-based routing, and more.',        stars: 125 },
  { id: 6,  name: 'Nuxt',         category: 'Framework', description: 'An intuitive Vue framework for building server-side rendered and static web applications.',                      stars: 54  },
  { id: 7,  name: 'Astro',        category: 'Framework', description: 'Build fast content-focused websites using an island architecture that ships zero JS by default.',                stars: 45  },
  { id: 8,  name: 'TypeScript',   category: 'Language',  description: 'A strongly typed superset of JavaScript that adds compile-time type checking and better tooling.',               stars: 99  },
  { id: 9,  name: 'Vite',         category: 'Tool',      description: 'Next-generation frontend tooling with instant dev server start and lightning-fast Hot Module Replacement.',      stars: 67  },
  { id: 10, name: 'webpack',      category: 'Tool',      description: 'A static module bundler for JavaScript with a powerful plugin and loader ecosystem.',                            stars: 64  },
  { id: 11, name: 'Rollup',       category: 'Tool',      description: 'A module bundler for JavaScript that compiles small pieces of code into larger libraries or applications.',      stars: 25  },
  { id: 12, name: 'ESLint',       category: 'Tool',      description: 'A pluggable linter for identifying and fixing patterns in JavaScript and TypeScript code.',                       stars: 24  },
  { id: 13, name: 'Prettier',     category: 'Tool',      description: 'An opinionated code formatter that enforces a consistent style across your entire codebase.',                    stars: 49  },
  { id: 14, name: 'Tailwind CSS', category: 'Library',   description: 'A utility-first CSS framework for rapidly building custom user interfaces without leaving your HTML.',           stars: 82  },
  { id: 15, name: 'Zustand',      category: 'Library',   description: 'A small, fast, and scalable state management solution built on simplified flux principles.',                     stars: 47  },
  { id: 16, name: 'React Query',  category: 'Library',   description: 'Powerful async state management for fetching, caching, and synchronising server state in React.',               stars: 42  },
  { id: 17, name: 'Redux',        category: 'Library',   description: 'A predictable state container for JS apps with strict unidirectional data flow and time-travel debugging.',      stars: 60  },
  { id: 18, name: 'Sass',         category: 'Language',  description: 'A mature CSS preprocessor adding variables, nesting, mixins, and functions to standard CSS.',                   stars: 15  },
  { id: 19, name: 'Vitest',       category: 'Tool',      description: 'A blazing-fast unit test framework powered by Vite with native ESM and TypeScript support.',                    stars: 13  },
  { id: 20, name: 'Storybook',    category: 'Tool',      description: 'A frontend workshop for building, documenting, and testing UI components in complete isolation.',                stars: 83  },
]

const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms))

// Simulates variable network + processing latency to expose race conditions.
// Delay varies by query length (150-500 ms range).
export async function searchItems(query: string): Promise<Item[]> {
  await sleep(150 + (query.length % 7) * 50)

  const q = query.trim().toLowerCase()
  if (!q) return [...ITEMS]

  return ITEMS.filter(
    item =>
      item.name.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
  )
}

export { ITEMS }
