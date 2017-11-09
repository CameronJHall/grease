from tgt_grease.core import GreaseContainer
from tgt_grease.core import ImportTool
from .Configuration import PrototypeConfig
from .BaseSource import BaseSourceClass
from .DeDuplication import Deduplication
from uuid import uuid4


class Scan(object):
    """Scanning class for GREASE Scanner

    This is the model to actually utilize the scanners to parse the configured environments

    Attributes:
        ioc (GreaseContainer): IOC for scanning
        conf (PrototypeConfig): Prototype configuration instance
        impTool (ImportTool): Import Utility Instance
        dedup (Deduplication): Deduplication instance to be used

    """

    def __init__(self, ioc=None):
        if ioc and isinstance(ioc, GreaseContainer):
            self.ioc = ioc
        else:
            self.ioc = GreaseContainer()
        self.conf = PrototypeConfig(self.ioc)
        self.impTool = ImportTool(self.ioc.getLogger())
        self.dedup = Deduplication(self.ioc)

    def Parse(self, source=None, config=None):
        """This will read all configurations and attempt to scan the environment

        This is the primary business logic for scanning in GREASE. This method will use configurations to parse
        the environment and attempt to schedule

        Note:
            If a Source is specified then *only* that source is parsed. If a configuration is set then *only* that
            configuration is parsed. If both are provided then the configuration will *only* be parsed if it is of
            the source provided

        Args:
            source (str): If set will only parse for the source listed
            config (str): If set will only parse the specified config

        Returns:
            bool: True unless error

        """
        self.ioc.getLogger().trace("Starting Parse of Environment", trace=True)
        Configuration = self.generate_config_set(source=source, config=config)
        for conf in Configuration:
            inst = self.impTool.load(conf.get('source', str(uuid4())))
            if not isinstance(inst, BaseSourceClass):
                self.ioc.getLogger().error("Invalid Source [{0}]".format(conf.get('source')), notify=False)
            else:
                if inst.parse_source(conf):
                    # send to scheduling after deduplication
                    # TODO: Mocking
                    data = self.dedup.Deduplicate(inst.get_data(), 'DeDup_Sourcing')
                    del inst
                    continue
                else:
                    self.ioc.getLogger().warning("Source [{0}] parsing failed".format(conf.get('source')), notify=False)
                    del inst
        return True

    def generate_config_set(self, source=None, config=None):
        """Examines configuration and returns list of configs to parse

        Note:
            If a Source is specified then *only* that source is parsed. If a configuration is set then *only* that
            configuration is parsed. If both are provided then the configuration will *only* be parsed if it is of
            the source provided

        Args:
            source (str): If set will only parse for the source listed
            config (str): If set will only parse the specified config

        Returns:
            list[dict]: Returns Configurations to Parse for data

        """
        ConfigList = []
        if source and config:
            if self.conf.get_config(config).get('source') == source:
                ConfigList.append(self.conf.get_config(config))
                return ConfigList
            else:
                self.ioc.getLogger().warning(
                    "Configuration [{0}] Not Found With Correct Source [{1}]".format(config, source),
                    trace=True,
                    notify=False
                )
        elif source and not config:
            if source in self.conf.get_sources():
                for configuration in self.conf.get_source(source):
                    ConfigList.append(configuration)
                return ConfigList
            else:
                self.ioc.getLogger().warning(
                    "Source not found in Configuration [{0}]".format(source),
                    trace=True,
                    notify=False
                )
        elif not source and config:
            if self.conf.get_config(config):
                ConfigList.append(self.conf.get_config(config))
                return ConfigList
            else:
                self.ioc.getLogger().warning(
                    "Config not found in Configuration [{0}]".format(config),
                    trace=True,
                    notify=False
                )
        else:
            ConfigList = self.conf.getConfiguration().get('raw')
        return ConfigList
