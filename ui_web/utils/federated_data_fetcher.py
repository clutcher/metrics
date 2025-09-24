import asyncio
from typing import List, Any, Callable, TypeVar

T = TypeVar('T')


class FederatedDataFetcher:
    def __init__(self, base_fetcher: Callable[[], Any]):
        self.base_fetcher = base_fetcher
        self.attribute_resolvers = []
        self.foreach_populators = []
        self.post_processors = []

    @classmethod
    def for_(cls, base_fetcher: Callable[[], Any]) -> 'FederatedDataFetcher':
        return cls(base_fetcher)
    
    def with_attribute(self, attr_name: str, resolver_fn: Callable[[Any], Any]) -> 'FederatedDataFetcher':
        self.attribute_resolvers.append((attr_name, resolver_fn))
        return self
    
    def with_foreach_populator(self, populator_fn: Callable[[Any], Any]) -> 'FederatedDataFetcher':
        self.foreach_populators.append(populator_fn)
        return self
    
    def with_result_post_processor(self, post_processor_fn: Callable[[Any], Any]) -> 'FederatedDataFetcher':
        self.post_processors.append(post_processor_fn)
        return self
    
    async def fetch(self) -> Any:
        base_data = await self.base_fetcher()

        is_list = isinstance(base_data, list)
        items = base_data if is_list else [base_data]

        if items:
            await asyncio.gather(
                self._apply_foreach_populators(items),
                self._apply_attribute_resolvers(items)
            )

        result = base_data
        if self.post_processors:
            for post_processor in self.post_processors:
                result = await self._apply_post_processor(result, post_processor)

        return result
    
    async def _apply_foreach_populators(self, items: List[Any]) -> None:
        if not self.foreach_populators:
            return

        for populator in self.foreach_populators:
            async def process_item(item):
                if asyncio.iscoroutinefunction(populator):
                    return await populator(item)
                else:
                    return populator(item)

            populator_tasks = [process_item(item) for item in items]
            await asyncio.gather(*populator_tasks)
    
    async def _apply_attribute_resolvers(self, items: List[Any]) -> None:
        if not self.attribute_resolvers:
            return
        
        resolver_tasks = []
        
        for attr_name, resolver_fn in self.attribute_resolvers:
            if hasattr(resolver_fn, 'batch_resolve'):
                task = self._apply_batch_resolver(items, attr_name, resolver_fn)
            else:
                task = self._apply_individual_resolver(items, attr_name, resolver_fn)
            
            resolver_tasks.append(task)
        
        await asyncio.gather(*resolver_tasks)
    
    @staticmethod
    async def _apply_batch_resolver(items: List[Any], attr_name: str, resolver_fn: Any) -> None:
        results = await resolver_fn.batch_resolve(items)
        for item, result in zip(items, results):
            setattr(item, attr_name, result)
    
    @staticmethod
    async def _apply_individual_resolver(items: List[Any], attr_name: str, resolver_fn: Callable[[Any], Any]) -> None:
        async def resolve_for_item(item):
            result = await resolver_fn(item)
            setattr(item, attr_name, result)
        
        item_tasks = [resolve_for_item(item) for item in items]
        await asyncio.gather(*item_tasks)
    
    @staticmethod
    async def _apply_post_processor(data: Any, post_processor_fn: Callable[[Any], Any]) -> Any:
        if asyncio.iscoroutinefunction(post_processor_fn):
            return await post_processor_fn(data)
        else:
            return post_processor_fn(data)