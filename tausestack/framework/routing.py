import os
import importlib.util
import logging # Added for logging
from fastapi import FastAPI, APIRouter, Request, HTTPException, status, Response as FastAPIResponse, params # Added FastAPI for type hint
from fastapi.routing import APIRoute
from typing import Any, Callable, Coroutine, Dict, List, Optional, Sequence, Type, Union, Set
from enum import Enum
from fastapi.datastructures import Default
from fastapi.types import IncEx
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute # Not strictly needed here but good for context
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from starlette.types import ASGIApp, Receive, Scope, Send # For broader ASGI compatibility if needed

logger = logging.getLogger("tausestack.framework.routing")


class TauseStackRoute(APIRoute):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Extract tags before calling super, as super might consume them or FastAPI might process them internally.
        # However, APIRoute's __init__ expects 'tags' as a direct keyword argument if provided.
        # The 'tags' kwarg should be passed to super().__init__.
        
        route_tags = kwargs.get('tags', [])
        auth_tag = "TAUSESTACK_AUTH_REQUIRED"
        
        if auth_tag in route_tags:
            self.is_auth_explicitly_required: bool = True
            # Optionally, remove the tag if it's purely internal and shouldn't be in OpenAPI docs.
            # If so, uncomment the following lines:
            # new_tags = [t for t in route_tags if t != auth_tag]
            # kwargs['tags'] = new_tags 
            # print(f"DEBUG TauseStackRoute.__init__: Auth tag found, setting is_auth_explicitly_required=True for path {kwargs.get('path')}")
        else:
            self.is_auth_explicitly_required: bool = False
            # print(f"DEBUG TauseStackRoute.__init__: Auth tag NOT found, setting is_auth_explicitly_required=False for path {kwargs.get('path')}")

        super().__init__(*args, **kwargs) # Pass original or modified kwargs
        # self.parent_router_for_debug: Optional[APIRouter] = None # For debugging if needed
        # print(f"DEBUG TauseStackRoute.__init__ final: Path {self.path}, Auth Required: {self.is_auth_explicitly_required}, Tags: {self.tags}")

    def get_route_handler(self) -> Callable[[StarletteRequest], Coroutine[Any, Any, StarletteResponse]]:
        # # --- DIAGNOSTIC PRINT AT SETUP TIME ---
        # print(f"\nDEBUG TauseStackRoute.get_route_handler (SETUP): Path: {self.path}")
        # print(f"DEBUG TauseStackRoute.get_route_handler (SETUP): self is {type(self)} (id: {id(self)})")
        # current_router_at_setup = getattr(self, 'router', 'NOT_SET_YET_OR_NONE')
        # if current_router_at_setup != 'NOT_SET_YET_OR_NONE' and current_router_at_setup is not None:
        #     print(f"DEBUG TauseStackRoute.get_route_handler (SETUP): self.router is {type(current_router_at_setup)} (id: {id(current_router_at_setup)})")
        #     # Check if it's a TauseStackRouter and print its auth_required flag
        #     if isinstance(current_router_at_setup, TauseStackRouter):
        #         print(f"DEBUG TauseStackRoute.get_route_handler (SETUP): self.router.auth_required = {getattr(current_router_at_setup, 'auth_required', 'NOT_FOUND_ON_ROUTER_AT_SETUP')}")
        #     else:
        #         print(f"DEBUG TauseStackRoute.get_route_handler (SETUP): self.router is not a TauseStackRouter, type is {type(current_router_at_setup)}")
        # else:
        #     print(f"DEBUG TauseStackRoute.get_route_handler (SETUP): self.router is {current_router_at_setup}")
        # # --- END DIAGNOSTIC PRINT ---

        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: StarletteRequest) -> StarletteResponse:
            # router = getattr(self, 'router', None) # This is self.router, which should be the TauseStackRouter instance
            
            # # --- BEGIN DEBUG PRINTS ---
            # print(f"\nDEBUG TauseStackRoute: Path: {self.path}")
            # print(f"DEBUG TauseStackRoute: self (TauseStackRoute instance) is {type(self)} (id: {id(self)})")
            # if router is not None:
            #     # The old self.router debug prints are less relevant now if we rely on is_auth_explicitly_required
            #     # but we can keep them for a bit to see if self.router ever gets set.
            #     print(f"DEBUG TauseStackRoute: (Old check) self.router is {type(router)} (id: {id(router)})")
            #     print(f"DEBUG TauseStackRoute: (Old check) isinstance(router, TauseStackRouter) = {isinstance(router, TauseStackRouter)}")
            #     print(f"DEBUG TauseStackRoute: (Old check) router.auth_required = {getattr(router, 'auth_required', 'NOT_FOUND_ON_ROUTER')}")
            # else:
            #     print(f"DEBUG TauseStackRoute: (Old check) self.router is None")
            # print(f"DEBUG TauseStackRoute: Request headers: {request.headers}")
            # # --- END DEBUG PRINTS ---

            # Determine if authentication is required for this route
            # route_requires_auth = False # Defaulted by getattr below
            # Use the explicitly set flag
            route_requires_auth = getattr(self, 'is_auth_explicitly_required', False)
            
            # # --- Update DEBUG PRINTS to reflect the new logic ---
            # print(f"DEBUG TauseStackRoute: self.is_auth_explicitly_required = {route_requires_auth}")
            
            # print(f"DEBUG TauseStackRoute: Determined route_requires_auth = {route_requires_auth}")

            if route_requires_auth:
                if not request.headers.get("X-Authenticated-User"):
                    # print(f"DEBUG TauseStackRoute: Auth required and X-Authenticated-User header MISSING. Returning 401.")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Not authenticated. Missing X-Authenticated-User header (simulated auth via TauseStackRoute)."}
                    )
                # else:
                    # print(f"DEBUG TauseStackRoute: Auth required and X-Authenticated-User header PRESENT.")
            # else:
                # print(f"DEBUG TauseStackRoute: Auth NOT required for this route.")
            
            return await original_route_handler(request)

        return custom_route_handler


class TauseStackRouter(APIRouter):
    def __init__(self, *, auth_required: bool = False, **kwargs: Any) -> None:
        super().__init__(route_class=TauseStackRoute, **kwargs)
        self.auth_required = auth_required

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Optional[Type[FastAPIResponse]] = Default(None), # Corrected type to FastAPIResponse
        name: Optional[str] = None,
        route_class_override: Optional[Type[APIRoute]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Optional[
            Callable[[APIRoute], str]
        ] = Default(None),
    ) -> APIRoute:
        # Call the original APIRouter's add_api_route method
        current_tags = list(tags) if tags is not None else []
        auth_tag = "TAUSESTACK_AUTH_REQUIRED"

        if self.auth_required:
            if auth_tag not in current_tags:
                current_tags.append(auth_tag)
            # print(f"DEBUG TauseStackRouter.add_api_route: Added {auth_tag} for path {path}")
        else:
            if auth_tag in current_tags:
                current_tags.remove(auth_tag)
            # print(f"DEBUG TauseStackRouter.add_api_route: Ensured no {auth_tag} for path {path}")

        return super().add_api_route(
            path,
            endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=current_tags, # Pass modified tags
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=methods,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema,
            response_class=response_class, # type: ignore
            name=name,
            route_class_override=route_class_override,
            callbacks=callbacks,
            openapi_extra=openapi_extra,
            generate_unique_id_function=generate_unique_id_function, # type: ignore
        )


def load_routers_from_directory(app: FastAPI, directory: str) -> List[str]:
    """
    Dynamically loads all APIRouter instances from .py files in a given directory.
    Assumes each relevant file has a 'router = APIRouter(...)' or 'router = TauseStackRouter(...)' line.
    Returns a list of successfully loaded module names.
    """
    loaded_modules: List[str] = []
    if not os.path.isdir(directory):
        logger.warning(f"Directory '{directory}' not found or is not a directory. Skipping router loading.")
        return loaded_modules

    try:
        filenames = os.listdir(directory)
    except FileNotFoundError:
        logger.warning(f"Directory '{directory}' not found. Skipping router loading.")
        return loaded_modules
    except Exception as e:
        logger.error(f"Error listing directory '{directory}': {e}. Skipping router loading.")
        return loaded_modules

    for filename in filenames:
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            file_path = os.path.join(directory, filename)
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    # Find the APIRouter instance in the loaded module
                    if hasattr(module, 'router'):
                        router_instance = getattr(module, 'router')
                        if isinstance(router_instance, APIRouter):
                            app.include_router(router_instance)
                            loaded_modules.append(module_name)
                            logger.debug(f"Successfully loaded router from {module_name}")
                        else:
                            logger.warning(f"'router' in {module_name} is not an APIRouter instance.")
                    else:
                        logger.warning(f"No 'router' attribute found in {module_name}.")
                except Exception as e:
                    logger.error(f"Error loading router from '{filename}': {e}") 
            else:
                logger.warning(f"Could not load module spec for {module_name}.")
    return loaded_modules
