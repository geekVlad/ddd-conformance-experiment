<?php

declare(strict_types=1);

use Deptrac\Deptrac\Contract\Config\Collector\DirectoryConfig;
use Deptrac\Deptrac\Contract\Config\DeptracConfig;
use Deptrac\Deptrac\Contract\Config\Layer;
use Deptrac\Deptrac\Contract\Config\Ruleset;

return static function (DeptracConfig $config): void {
    $target = getenv('DEPTRAC_TARGET');
    if (!is_string($target) || $target === '') {
        throw new RuntimeException('DEPTRAC_TARGET must point to a PHP repository.');
    }

    $config
        ->paths($target)
        ->excludeFiles('#/(?:vendor|tests?|Test|Tests|behat|fixtures?)/#')
        ->layers(
            $domain = Layer::withName('Domain')->collectors(
                DirectoryConfig::create('.*[\\/](?:Domain|domain)[\\/].*'),
            ),
            $application = Layer::withName('Application')->collectors(
                DirectoryConfig::create('.*[\\/](?:Application|application|UseCase|UseCases)[\\/].*'),
            ),
            $infrastructure = Layer::withName('Infrastructure')->collectors(
                DirectoryConfig::create('.*[\\/](?:Infrastructure|infrastructure|Infra|infra|Adapter|Adapters|Persistence)[\\/].*'),
            ),
        )
        ->rulesets(
            Ruleset::forLayer($domain)->accesses($domain),
            Ruleset::forLayer($application)->accesses($application, $domain),
            Ruleset::forLayer($infrastructure)->accesses($infrastructure, $application, $domain),
        )
    ;
};
