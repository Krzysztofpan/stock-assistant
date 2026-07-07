import type { QueryClient } from "@tanstack/react-query"

export function setInitialInfiniteQueryData<TPage>(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
  initialPage: TPage,
  initialPageParam: unknown = undefined,
) {
  queryClient.setQueryData(queryKey, {
    pages: [initialPage],
    pageParams: [initialPageParam],
  })
}

export function flattenInfinitePages<TItem, TPage>(
  pages: TPage[] | undefined,
  selectItems: (page: TPage) => TItem[],
  options?: { prependPages?: boolean },
): TItem[] {
  if (!pages) {
    return []
  }

  const orderedPages = options?.prependPages ? [...pages].reverse() : pages

  return orderedPages.flatMap(selectItems)
}
