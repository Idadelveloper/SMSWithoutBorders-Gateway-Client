#!/usr/bin/env python3

import logging
import threading
import time
from deku import Deku

from common.mmcli_python.modem import Modem

class ModemManager:
    """Summary of ModemManager
    Attributes:
    """
    def __init__(self, daemon_sleep_time:int=3)->None:
        """Initialize a modem manager instance.
        """
        self.models = []
        self.daemon_sleep_time=daemon_sleep_time
        self.active_nodes = {}

    def add_model(self, model) -> None:
        """Add model to daemon.

        The `main()` would be called for each model included.

            Args:
                model: 
                    DataType (any class) which has a method called `main`
                    that will be called by the daemon thread
        """
        self.models.append(model)

    def daemon(self) -> None:
        """Binds modems to models

        Monitors I/O changes of modem. Once a modem is active, it gets 
        added to the list of active nodes. 
        For each active node, the requested model will be triggered for them.

            Args:
                model: 
                    Any class that extends model class 
                    daemon_sleep_time: How long the daemon should sleep thread
                    after listening

            Returns: None
        """

        logging.debug("initializing modem manager daemon")

        try:
            th_hardware_state_monitor = threading.Thread( 
                    target=self.__daemon_hardware_state__, 
                    daemon=True)
        except Exception as error:
            raise error
        else:
            try:
                th_hardware_state_monitor.start()

                # if state dies, no need for active
                th_hardware_state_monitor.join()
            except Exception as error:
                raise error

    def __refresh_nodes__(self, available_modems)->None:
        """Checks HW available modems against active running nodes
        """
        modems = [modem.imei for modem in available_modems]
        active_nodes = self.active_nodes.keys()
        not_active = list(set(active_nodes).difference(modems))
        logging.debug("inactive nodes: %s", not_active)

        for modem_imei in not_active:
            try:
                for _, thread_model in self.active_nodes[modem_imei].items():
                    thread_model[1].set()
                del self.active_nodes[modem_imei]
                logging.debug("removed modem %s", modem_imei)
            except Exception as error:
                logging.exception(error)
        logging.debug("refreshed nodes")


    def __daemon_hardware_state__(self) -> None:
        while True:
            try:
                available_modems, locked_modems,_ = Deku.get_available_modems()
                logging.debug("+ Available modems %s Locked modems %s", 
                        [modem.index for modem in available_modems], \
                        [modem.index for modem in locked_modems])

            except Exception as error:
                raise error

            else:
                try:
                    self.__add_nodes__(modems=available_modems, 
                            locked_modems=locked_modems)
                    self.__refresh_nodes__(available_modems + locked_modems)
                except Exception as error:
                    raise error

            finally:
                logging.debug("sleeping hardware monitor daemon")
                time.sleep(self.daemon_sleep_time)

    def __add_nodes__(self, modems:list(), 
            locked_modems=list()) -> None:
        logging.debug("# of models %d", len(self.models))

        for _model in self.models:
            # logging.debug("working with model %s", _model)

            # some incoming doesn't need modems locked
            if hasattr(_model, 'locked_modems') and _model.locked_modems:
                modems += locked_modems

            for modem in modems:
                model = _model.init(modem=modem)
                if modem.imei in self.active_nodes and \
                        model.__class__.__name__ in self.active_nodes[modem.imei]:
                    """
                    if not Deku.modem_ready(modem) or (
                            hasattr(_model, 'locked_modems') and not _model.locked_modems):
                        continue
                    """
                    logging.debug("modem [%s] %s already active for %s",
                            modem.imei, modem.index, _model)
                    continue

                logging.debug("initializing modem for %s %s", 
                        modem.imei, _model)

                modem_thread = threading.Thread(
                        target=model.main)
                modem_thread.start()
                logging.debug("started %s for %s", modem.imei, model)
                self.active_nodes[modem.imei] = {
                        model.__class__.__name__: (modem_thread, model) }

                logging.debug("added %s to active nodes %s", 
                        modem.imei, model.__class__.__name__)