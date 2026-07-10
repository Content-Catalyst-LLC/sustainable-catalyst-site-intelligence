<?php
/**
 * Plugin Name: Sustainable Catalyst Site Intelligence
 * Description: Connects Sustainable Catalyst pages to the Site Intelligence backend, GA4/dataLayer custom events, and shortcode dashboards.
 * Version: 1.3.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

final class SC_Site_Intelligence_Plugin {
    const OPTION_KEY = 'sc_site_intelligence_options';
    const VERSION = '1.3.0';
    const REST_NAMESPACE = 'sc-site-intelligence/v1';

    public function __construct() {
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_shortcode('sc_site_intelligence_dashboard', [$this, 'dashboard_shortcode']);
        add_shortcode('sc_site_intelligence_page', [$this, 'page_shortcode']);
        add_shortcode('sc_site_intelligence_unmapped', [$this, 'unmapped_shortcode']);
        add_shortcode('sc_site_intelligence_events', [$this, 'events_shortcode']);
        add_shortcode('sc_site_intelligence_opportunities', [$this, 'opportunities_shortcode']);
        add_shortcode('sc_external_data_health', [$this, 'external_health_shortcode']);
        add_shortcode('sc_climate_energy_intelligence', [$this, 'climate_energy_shortcode']);
        add_shortcode('sc_external_cache_status', [$this, 'external_cache_shortcode']);
        add_shortcode('sc_search_intelligence', [$this, 'search_intelligence_shortcode']);
        add_shortcode('sc_search_opportunities', [$this, 'search_opportunities_shortcode']);
        add_shortcode('sc_metadata_intelligence', [$this, 'metadata_intelligence_shortcode']);
        add_shortcode('sc_internal_link_intelligence', [$this, 'internal_link_intelligence_shortcode']);
        add_shortcode('sc_seo_recommendations', [$this, 'seo_recommendations_shortcode']);
        add_shortcode('sc_indexing_intelligence', [$this, 'indexing_intelligence_shortcode']);
        add_shortcode('sc_sitemap_coverage', [$this, 'sitemap_coverage_shortcode']);
        add_shortcode('sc_404_intelligence', [$this, 'four_oh_four_intelligence_shortcode']);
        add_shortcode('sc_content_strategy_intelligence', [$this, 'content_strategy_shortcode']);
        add_shortcode('sc_topic_momentum', [$this, 'topic_momentum_shortcode']);
        add_shortcode('sc_update_priorities', [$this, 'update_priorities_shortcode']);
        add_shortcode('sc_publishing_opportunities', [$this, 'publishing_opportunities_shortcode']);
        add_shortcode('sc_site_intelligence_public_landing', [$this, 'public_landing_shortcode']);
        add_shortcode('sc_site_intelligence_public_flagship', [$this, 'public_flagship_shortcode']);
        add_shortcode('sc_site_intelligence_public_page_builder', [$this, 'public_page_builder_shortcode']);
        add_shortcode('sc_public_dashboard_shortcode_bundle', [$this, 'public_shortcode_bundle_shortcode']);
        add_shortcode('sc_public_dashboard_visual_qa', [$this, 'public_visual_qa_shortcode']);
        add_shortcode('sc_public_site_intelligence', [$this, 'public_site_intelligence_shortcode']);
        add_shortcode('sc_public_knowledge_overview', [$this, 'public_knowledge_overview_shortcode']);
        add_shortcode('sc_public_climate_energy_summary', [$this, 'public_climate_energy_summary_shortcode']);
        add_shortcode('sc_public_methodology', [$this, 'public_methodology_shortcode']);
        add_shortcode('sc_public_dashboard_directory', [$this, 'public_dashboard_directory_shortcode']);
        add_shortcode('sc_public_dashboard_navigation', [$this, 'public_dashboard_navigation_shortcode']);
        add_shortcode('sc_public_topic_page_templates', [$this, 'public_topic_page_templates_shortcode']);
        add_shortcode('sc_public_topic_page_visual_qa', [$this, 'public_topic_page_visual_qa_shortcode']);
        add_shortcode('sc_public_api_sources', [$this, 'public_api_sources_shortcode']);
        add_shortcode('sc_public_source_health', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_development_indicators', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_research_metadata', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_publication_metadata', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_repository_intelligence', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_indicator_overview', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_sustainability_indicators', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_source_page_directory', [$this, 'public_source_page_directory_shortcode']);
        add_shortcode('sc_public_source_navigation', [$this, 'public_source_navigation_shortcode']);
        add_shortcode('sc_public_source_page_templates', [$this, 'public_source_page_templates_shortcode']);
        add_shortcode('sc_public_source_page_visual_qa', [$this, 'public_source_page_visual_qa_shortcode']);
        add_shortcode('sc_public_connector_status', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_cache_status', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_source_freshness', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_world_bank_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_openalex_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_crossref_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_github_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_environmental_connectors', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_climate_energy_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_environmental_monitoring_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_biodiversity_land_use_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_knowledge_system_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_search_discovery_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_source_methodology', [$this, 'public_source_methodology_shortcode']);
        add_shortcode('sc_public_dashboard_readiness', [$this, 'public_dashboard_readiness_shortcode']);
        add_shortcode('sc_advanced_external_data_health', [$this, 'advanced_external_health_shortcode']);
        add_shortcode('sc_environmental_monitoring_intelligence', [$this, 'environmental_monitoring_shortcode']);
        add_shortcode('sc_urban_resilience_intelligence', [$this, 'urban_resilience_shortcode']);
        add_shortcode('sc_biodiversity_land_use_intelligence', [$this, 'biodiversity_land_use_shortcode']);
        add_shortcode('sc_energy_systems_intelligence', [$this, 'energy_systems_shortcode']);
        add_shortcode('sc_site_intelligence_report', [$this, 'site_intelligence_report_shortcode']);
        add_shortcode('sc_search_intelligence_report', [$this, 'search_intelligence_report_shortcode']);
        add_shortcode('sc_content_strategy_report', [$this, 'content_strategy_report_shortcode']);
        add_shortcode('sc_external_sources_report', [$this, 'external_sources_report_shortcode']);
        add_shortcode('sc_climate_energy_report', [$this, 'climate_energy_report_shortcode']);
        add_shortcode('sc_indexing_report', [$this, 'indexing_report_shortcode']);
        add_shortcode('sc_report_export_bundle', [$this, 'report_export_bundle_shortcode']);
        add_shortcode('sc_ai_brief_status', [$this, 'ai_brief_status_shortcode']);
        add_shortcode('sc_ai_site_intelligence_brief', [$this, 'ai_site_intelligence_brief_shortcode']);
        add_shortcode('sc_ai_search_brief', [$this, 'ai_search_brief_shortcode']);
        add_shortcode('sc_ai_publishing_brief', [$this, 'ai_publishing_brief_shortcode']);
        add_shortcode('sc_ai_external_sources_brief', [$this, 'ai_external_sources_brief_shortcode']);
        add_shortcode('sc_ai_public_dashboard_brief', [$this, 'ai_public_dashboard_brief_shortcode']);
        add_shortcode('sc_site_intelligence_admin_overview', [$this, 'admin_overview_shortcode']);
        add_shortcode('sc_site_intelligence_shortcode_catalog', [$this, 'shortcode_catalog_shortcode']);
        add_shortcode('sc_site_intelligence_module_status', [$this, 'module_status_shortcode']);
        add_shortcode('sc_site_intelligence_diagnostic_summary', [$this, 'diagnostic_summary_shortcode']);
        add_shortcode('sc_site_intelligence_connection_check', [$this, 'connection_check_shortcode']);
        add_shortcode('sc_site_intelligence_release_status', [$this, 'release_status_shortcode']);
    }

    public static function defaults() {
        return [
            'backend_url' => '',
            'api_token' => '',
            'enable_event_bridge' => '1',
            'enable_dashboard' => '1',
        ];
    }

    public static function options() {
        return wp_parse_args(get_option(self::OPTION_KEY, []), self::defaults());
    }

    public function admin_menu() {
        add_options_page(
            'SC Site Intelligence',
            'SC Site Intelligence',
            'manage_options',
            'sc-site-intelligence',
            [$this, 'settings_page']
        );
    }

    public function register_settings() {
        register_setting('sc_site_intelligence', self::OPTION_KEY, [
            'type' => 'array',
            'sanitize_callback' => [$this, 'sanitize_options'],
        ]);
    }

    public function sanitize_options($input) {
        $defaults = self::defaults();
        $output = [];
        $output['backend_url'] = isset($input['backend_url']) ? esc_url_raw(trim($input['backend_url'])) : $defaults['backend_url'];
        $output['api_token'] = isset($input['api_token']) ? sanitize_text_field($input['api_token']) : $defaults['api_token'];
        $output['enable_event_bridge'] = !empty($input['enable_event_bridge']) ? '1' : '0';
        $output['enable_dashboard'] = !empty($input['enable_dashboard']) ? '1' : '0';
        return $output;
    }

    public function register_rest_routes() {
        register_rest_route(self::REST_NAMESPACE, '/dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/page', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_page'],
            'permission_callback' => '__return_true',
            'args' => [
                'path' => [
                    'required' => true,
                    'sanitize_callback' => 'sanitize_text_field',
                ],
            ],
        ]);
        register_rest_route(self::REST_NAMESPACE, '/unmapped', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_unmapped'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/events', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_events'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_opportunities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/conversions', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_conversions'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/external-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_external_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/external-cache', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_external_cache'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/climate-energy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_climate_energy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_opportunities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/metadata-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_metadata_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/internal-link-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_internal_link_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/seo-recommendations', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_seo_recommendations'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/indexing-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_indexing_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/sitemap-coverage', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_sitemap_coverage'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/404-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_404_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/indexing-recommendations', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_indexing_recommendations'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/content-strategy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_content_strategy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/topic-momentum', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_topic_momentum'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/update-priorities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_update_priorities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/publishing-opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_publishing_opportunities'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-landing-page', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_landing_page'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-shortcodes', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_shortcodes'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-readiness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_readiness'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_visual_qa'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-knowledge-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_knowledge_overview'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-climate-energy-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_climate_energy_summary'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-methodology', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_methodology'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-directory', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard_directory'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-methodology', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_methodology'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-navigation', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard_navigation'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-page-templates', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_page_templates'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-page-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_page_visual_qa'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-api-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_api_sources'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-development-indicators', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_development_indicators'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-research-metadata', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_research_metadata'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-publication-metadata', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_publication_metadata'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-repository-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_repository_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-indicator-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_indicator_overview'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainability-indicators', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_sustainability_indicators'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-pages', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_pages'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-navigation', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_navigation'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-page-templates', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_page_templates'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-page-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_page_visual_qa'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-connector-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-cache-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_cache_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-freshness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_freshness'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-connector-detail', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_detail'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-readiness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_readiness'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);

        register_rest_route(self::REST_NAMESPACE, '/advanced-external-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_advanced_external_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/environmental-monitoring', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_environmental_monitoring'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/urban-resilience', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_urban_resilience'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/biodiversity-land-use', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_biodiversity_land_use'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/energy-systems', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_energy_systems'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/report-site-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_site_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-search-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_search_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-content-strategy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_content_strategy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-external-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_external_sources'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-climate-energy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_climate_energy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-indexing', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_indexing'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-export', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_export'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/reports-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_reports_summary'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/ai-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-site-intelligence-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_site_intelligence_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-search-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_search_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-publishing-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_publishing_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-external-sources-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_external_sources_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-public-dashboard-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_public_dashboard_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-briefs-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_briefs_summary'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/admin-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_overview'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-registry', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_registry'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_sources'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-modules', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_modules'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-shortcodes', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_shortcodes'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-diagnostics', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_diagnostics'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-visibility', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_visibility'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-source-control', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_source_control'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_status'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-connection-check', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_connection_check'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-public-readiness-check', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_public_readiness_check'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-diagnostic-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_diagnostic_summary'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/release-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_release_status'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/release-smoke-test', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_release_smoke_test'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/event', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [$this, 'rest_event'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/diagnostics/ga4', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ga4_diagnostics'],
            'permission_callback' => '__return_true',
        ]);
    }

    private function safe_backend_error_message($raw_body, $fallback = 'Site Intelligence backend returned an error.') {
        $raw_body = is_string($raw_body) ? $raw_body : '';
        if ($raw_body === '') {
            return $fallback;
        }
        if (stripos($raw_body, '<!DOCTYPE') !== false || stripos($raw_body, '<html') !== false || stripos($raw_body, 'cloudflare') !== false || stripos($raw_body, 'bad gateway') !== false) {
            return 'Site Intelligence backend or site proxy returned a gateway error. Try the direct Render endpoint, then redeploy or retry the WordPress proxy after the origin is healthy.';
        }
        return sanitize_text_field(wp_trim_words(wp_strip_all_tags($raw_body), 24, '…'));
    }

    private function backend_request($endpoint, $method = 'GET', $body = null) {
        $options = self::options();
        if (empty($options['backend_url'])) {
            return new WP_Error('scsi_no_backend', 'Site Intelligence backend URL is not configured.', ['status' => 400]);
        }
        $url = untrailingslashit($options['backend_url']) . '/' . ltrim($endpoint, '/');
        $args = [
            'method' => $method,
            'timeout' => 12,
            'headers' => [
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
            ],
        ];
        if (!empty($options['api_token'])) {
            $args['headers']['X-SC-Intelligence-Token'] = $options['api_token'];
        }
        if (!is_null($body)) {
            $args['body'] = wp_json_encode($body);
        }
        $response = wp_remote_request($url, $args);
        if (is_wp_error($response)) {
            return $response;
        }
        $code = wp_remote_retrieve_response_code($response);
        $raw_body = wp_remote_retrieve_body($response);
        $payload = json_decode($raw_body, true);
        if ($code < 200 || $code >= 300) {
            $message = 'Site Intelligence backend returned an error.';
            if (is_array($payload) && isset($payload['detail'])) {
                if (is_array($payload['detail']) && isset($payload['detail']['message'])) {
                    $message = sanitize_text_field($payload['detail']['message']);
                } elseif (is_string($payload['detail'])) {
                    $message = sanitize_text_field($payload['detail']);
                }
            } elseif (!empty($raw_body)) {
                $message = $this->safe_backend_error_message($raw_body);
            }
            return new WP_Error('scsi_backend_error', $message, [
                'status' => $code,
                'payload' => is_array($payload) ? $payload : null,
            ]);
        }
        return is_array($payload) ? $payload : ['ok' => true, 'raw' => $raw_body];
    }

    public function rest_dashboard(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/dashboard' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_page(WP_REST_Request $request) {
        $path = sanitize_text_field($request->get_param('path'));
        $endpoint = 'intelligence/page?' . http_build_query(['path' => $path]);
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_ga4_diagnostics(WP_REST_Request $request) {
        $result = $this->backend_request('diagnostics/ga4');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_unmapped(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/unmapped' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_events(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/event-diagnostics' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_opportunities(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/page-opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_conversions(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/conversions' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_external_health(WP_REST_Request $request) {
        $query = [];
        if ($request->get_param('force_refresh')) {
            $query['force_refresh'] = sanitize_text_field($request->get_param('force_refresh'));
        }
        $endpoint = 'external/health' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_external_cache(WP_REST_Request $request) {
        $result = $this->backend_request('external/cache');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_climate_energy(WP_REST_Request $request) {
        $query = [];
        foreach (['latitude', 'longitude', 'country', 'start', 'end', 'year', 'force_refresh'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/dashboards/climate-energy' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        $endpoint = 'intelligence/search' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_opportunities(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'search/opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_health(WP_REST_Request $request) {
        $result = $this->backend_request('search/health');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_metadata_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/metadata' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_internal_link_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/internal-links' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_seo_recommendations(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/recommendations' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }


    public function rest_indexing_intelligence(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/indexing' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_sitemap_coverage(WP_REST_Request $request) {
        $result = $this->backend_request('indexing/sitemap');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_404_intelligence(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'indexing/404s' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_indexing_recommendations(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'indexing/recommendations' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    private function publishing_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'prior_start_date', 'prior_end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_content_strategy(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/content-strategy' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_topic_momentum(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/topic-momentum' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_update_priorities(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/update-priorities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_publishing_opportunities(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/promotion-opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }


    private function public_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'latitude', 'longitude', 'country', 'start', 'end', 'year', 'live'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_public_landing_page(WP_REST_Request $request) {
        $result = $this->backend_request('public/landing-page');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return $result;
    }


    public function rest_public_page_builder(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_shortcodes(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/shortcodes');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_readiness(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/readiness');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_visual_qa(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/visual-qa');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_dashboard(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/dashboard' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_knowledge_overview(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/knowledge-overview' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_climate_energy_summary(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/climate-energy-summary' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_methodology(WP_REST_Request $request) {
        $result = $this->backend_request('public/methodology');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }


    public function rest_public_dashboard_directory(WP_REST_Request $request) {
        $result = $this->backend_request('public/dashboards');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_dashboard(WP_REST_Request $request) {
        $topic = sanitize_key($request->get_param('topic'));
        $allowed = ['climate-energy', 'environmental-monitoring', 'biodiversity-land-use', 'knowledge-system', 'search-discovery'];
        if (!in_array($topic, $allowed, true)) {
            return new WP_REST_Response(['ok' => false, 'message' => 'Unknown public topic dashboard.'], 400);
        }
        $result = $this->backend_request('public/dashboards/' . $topic);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_source_methodology(WP_REST_Request $request) {
        $result = $this->backend_request('public/source-methodology');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_dashboard_navigation(WP_REST_Request $request) {
        $current = sanitize_key($request->get_param('current'));
        $endpoint = 'public/navigation' . ($current ? '?current=' . rawurlencode($current) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_page_templates(WP_REST_Request $request) {
        $slug = sanitize_key($request->get_param('slug'));
        $endpoint = 'public/page-templates' . ($slug ? '?slug=' . rawurlencode($slug) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_page_visual_qa(WP_REST_Request $request) {
        $result = $this->backend_request('public/topic-page-visual-qa');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    private function public_source_endpoint_map($key) {
        $map = [
            'api_sources' => 'public/sources',
            'source_health' => 'public/sources/health',
            'development_indicators' => 'public/sources/development-indicators',
            'research_metadata' => 'public/sources/research-metadata',
            'publication_metadata' => 'public/sources/publications',
            'repository_intelligence' => 'public/sources/repositories',
            'indicator_overview' => 'public/indicators/overview',
            'sustainability_indicators' => 'public/indicators/sustainability',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/sources';
    }

    private function rest_public_source_panel($key) {
        $result = $this->backend_request($this->public_source_endpoint_map($key));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_api_sources(WP_REST_Request $request) { return $this->rest_public_source_panel('api_sources'); }
    public function rest_public_source_health(WP_REST_Request $request) { return $this->rest_public_source_panel('source_health'); }
    public function rest_public_development_indicators(WP_REST_Request $request) { return $this->rest_public_source_panel('development_indicators'); }
    public function rest_public_research_metadata(WP_REST_Request $request) { return $this->rest_public_source_panel('research_metadata'); }
    public function rest_public_publication_metadata(WP_REST_Request $request) { return $this->rest_public_source_panel('publication_metadata'); }
    public function rest_public_repository_intelligence(WP_REST_Request $request) { return $this->rest_public_source_panel('repository_intelligence'); }
    public function rest_public_indicator_overview(WP_REST_Request $request) { return $this->rest_public_source_panel('indicator_overview'); }
    public function rest_public_sustainability_indicators(WP_REST_Request $request) { return $this->rest_public_source_panel('sustainability_indicators'); }

    private function public_connector_endpoint_map($key) {
        $map = [
            'connector_status' => 'public/connectors/status',
            'cache_status' => 'public/connectors/cache',
            'source_freshness' => 'public/connectors/freshness',
            'world_bank' => 'public/connectors/world-bank',
            'openalex' => 'public/connectors/openalex',
            'crossref' => 'public/connectors/crossref',
            'github' => 'public/connectors/github',
            'environmental' => 'public/connectors/environmental',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/connectors/status';
    }

    private function rest_public_connector_panel($key) {
        $result = $this->backend_request($this->public_connector_endpoint_map($key));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_connector_status(WP_REST_Request $request) { return $this->rest_public_connector_panel('connector_status'); }
    public function rest_public_cache_status(WP_REST_Request $request) { return $this->rest_public_connector_panel('cache_status'); }
    public function rest_public_source_freshness(WP_REST_Request $request) { return $this->rest_public_connector_panel('source_freshness'); }

    public function rest_public_connector_detail(WP_REST_Request $request) {
        $slug = sanitize_key($request->get_param('slug'));
        $allowed = ['world-bank', 'openalex', 'crossref', 'github', 'environmental'];
        if (!in_array($slug, $allowed, true)) {
            return new WP_REST_Response(['ok' => false, 'message' => 'Unknown public connector slug.'], 400);
        }
        return $this->rest_public_connector_panel(str_replace('-', '_', $slug));
    }

    public function rest_public_readiness(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'intelligence/public-readiness' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }



    private function advanced_external_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['latitude', 'longitude', 'country', 'state', 'county', 'start', 'end', 'force_refresh'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_advanced_external_health(WP_REST_Request $request) {
        $query = [];
        if ($request->get_param('force_refresh')) { $query['force_refresh'] = sanitize_text_field($request->get_param('force_refresh')); }
        $endpoint = 'external/advanced/health' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_environmental_monitoring(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/environmental-monitoring' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_urban_resilience(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/urban-resilience' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_biodiversity_land_use(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/biodiversity-land-use' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_energy_systems(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/energy-systems' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }


    private function report_query_args(WP_REST_Request $request, $keys = []) {
        $query = [];
        foreach ($keys as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    private function proxy_report($endpoint, WP_REST_Request $request, $keys = []) {
        $query = $this->report_query_args($request, array_merge(['start_date', 'end_date', 'format'], $keys));
        $result = $this->backend_request($endpoint . (!empty($query) ? '?' . http_build_query($query) : ''));
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_report_site_intelligence(WP_REST_Request $request) {
        return $this->proxy_report('reports/site-intelligence', $request);
    }

    public function rest_report_search_intelligence(WP_REST_Request $request) {
        return $this->proxy_report('reports/search-intelligence', $request);
    }

    public function rest_report_content_strategy(WP_REST_Request $request) {
        return $this->proxy_report('reports/content-strategy', $request, ['prior_start_date', 'prior_end_date', 'limit']);
    }

    public function rest_report_external_sources(WP_REST_Request $request) {
        return $this->proxy_report('reports/external-sources', $request);
    }

    public function rest_report_climate_energy(WP_REST_Request $request) {
        return $this->proxy_report('reports/climate-energy', $request, ['latitude', 'longitude', 'country', 'start', 'end', 'year', 'live']);
    }

    public function rest_report_indexing(WP_REST_Request $request) {
        return $this->proxy_report('reports/indexing', $request);
    }

    public function rest_report_export(WP_REST_Request $request) {
        return $this->proxy_report('reports/export', $request, ['report']);
    }

    public function rest_reports_summary(WP_REST_Request $request) {
        $result = $this->backend_request('intelligence/reports');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }



    private function local_public_dashboard_ai_brief() {
        return [
            'ok' => true,
            'brief_id' => 'public-dashboard-ai-brief',
            'title' => 'AI-Assisted Public Dashboard Brief',
            'summary' => 'Interpret public-safe dashboard status, methodology notes, knowledge overview, and public release readiness.',
            'generated_at' => gmdate('c'),
            'mode' => 'public',
            'provider' => 'deterministic-local',
            'model' => 'wordpress-fallback-v1.3.0',
            'source_report' => [
                'report_id' => 'public-dashboard',
                'title' => 'Public Dashboard Readiness Report',
                'source' => ['dashboard' => 'wordpress-local-fallback', 'mode' => 'public-safe', 'live_analytics' => false],
                'date_range' => [],
            ],
            'executive_summary' => 'The Sustainable Catalyst public dashboard layer is suitable for reviewed public presentation when it uses sanitized, source-labeled summaries, methodology notes, and public-safe snapshots rather than raw analytics or live operational diagnostics.',
            'key_findings' => [
                'Public dashboard modules should remain aggregated, reviewed, and source-labeled.',
                'Raw GA4 analytics, conversion diagnostics, report queues, and operational notes should remain private.',
                'Public pages should use fast snapshots by default and reserve live connector calls for private testing.',
            ],
            'recommended_actions' => [
                'Use the public landing, public knowledge overview, climate/energy summary, and methodology shortcodes on public pages.',
                'Keep the Public Dashboard Brief deterministic unless directly testing the backend route.',
                'Review all public copy before promoting the dashboard as a flagship platform asset.',
                'Pair public summaries with clear educational and analytical boundaries.',
            ],
            'content_opportunities' => [
                'Create a public Site Intelligence landing page that explains the knowledge-system layer without exposing private analytics.',
                'Use the public dashboard as portfolio evidence for open infrastructure, analytics, and responsible sustainability tooling.',
                'Turn reviewed public dashboard findings into LinkedIn or Substack updates only after manual review.',
            ],
            'risk_notes' => [
                'Public dashboards should not expose raw analytics, private recommendations, API configuration, or backend diagnostic details.',
                'External-source summaries can be delayed, cached, or unavailable; public copy should describe source and freshness limits.',
                'This local fallback exists so the page remains stable even when Render, Bluehost, Cloudflare, or an AI provider is unavailable.',
            ],
            'public_safe_summary' => 'Public Site Intelligence can be presented as a reviewed, source-labeled dashboard framework for Sustainable Catalyst. It should emphasize methodology, knowledge architecture, public data context, and educational boundaries while keeping raw analytics and operational diagnostics private.',
            'private_notes' => [],
            'confidence' => [
                'level' => 'medium',
                'basis' => 'Generated from the v0.9.0 WordPress local fallback to avoid gateway-dependent public rendering.',
            ],
            'methodology' => [
                'summary' => 'v0.9.0 renders the public-dashboard brief locally by default to prevent gateway errors from affecting dashboard pages.',
                'privacy_note' => 'No raw analytics, external API calls, API tokens, or private report payloads are used in this fallback.',
            ],
        ];
    }

    private function ai_brief_query_args(WP_REST_Request $request, $keys = []) {
        $query = [];
        foreach ($keys as $key) {
            $value = $request->get_param($key);
            if ($value !== null && $value !== '') {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    private function proxy_ai_brief($endpoint, WP_REST_Request $request, $keys = []) {
        $query = $this->ai_brief_query_args($request, array_merge(['start_date', 'end_date', 'prior_start_date', 'prior_end_date', 'limit', 'mode', 'use_ai', 'format'], $keys));
        $result = $this->backend_request($endpoint . (!empty($query) ? '?' . http_build_query($query) : ''));
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_ai_status(WP_REST_Request $request) {
        $result = $this->backend_request('ai/status');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_ai_site_intelligence_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/site-intelligence', $request);
    }

    public function rest_ai_search_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/search', $request);
    }

    public function rest_ai_publishing_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/publishing', $request);
    }

    public function rest_ai_external_sources_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/external-sources', $request);
    }

    public function rest_ai_public_dashboard_brief(WP_REST_Request $request) {
        $live = $request->get_param('live');
        if ($live !== 'true' && $live !== '1') {
            return rest_ensure_response($this->local_public_dashboard_ai_brief());
        }
        $result = $this->proxy_ai_brief('ai/briefs/public-dashboard', $request);
        if (is_wp_error($result)) {
            return rest_ensure_response($this->local_public_dashboard_ai_brief());
        }
        return $result;
    }

    public function rest_ai_briefs_summary(WP_REST_Request $request) {
        $result = $this->backend_request('intelligence/ai-briefs');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    private function proxy_admin_control($endpoint) {
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_admin_overview(WP_REST_Request $request) {
        return $this->proxy_admin_control('intelligence/admin');
    }

    public function rest_admin_registry(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/registry');
    }

    public function rest_admin_sources(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/sources');
    }

    public function rest_admin_modules(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/modules');
    }

    public function rest_admin_shortcodes(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/shortcodes');
    }

    public function rest_admin_diagnostics(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/diagnostics');
    }

    public function rest_admin_visibility(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/visibility');
    }

    public function rest_admin_source_control(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/source-control');
    }


    public function rest_admin_status(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/status');
    }

    public function rest_admin_connection_check(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/connection-check');
    }

    public function rest_admin_public_readiness_check(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/public-readiness-check');
    }

    public function rest_admin_diagnostic_summary(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/diagnostic-summary');
    }

    public function rest_release_status(WP_REST_Request $request) {
        return $this->proxy_admin_control('release/status');
    }

    public function rest_release_smoke_test(WP_REST_Request $request) {
        return $this->proxy_admin_control('release/smoke-test');
    }

    public function rest_event(WP_REST_Request $request) {
        $body = json_decode($request->get_body(), true);
        if (!is_array($body)) {
            $body = [];
        }
        $body['page_path'] = isset($body['page_path']) ? sanitize_text_field($body['page_path']) : '/';
        $body['event_name'] = isset($body['event_name']) ? sanitize_key($body['event_name']) : 'sc_unknown_event';
        $result = $this->backend_request('collect/event', 'POST', $body);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        $options = self::options();
        ?>
        <div class="wrap scsi-admin-wrap">
            <h1>Sustainable Catalyst Site Intelligence</h1>
            <p>Connect Sustainable Catalyst to the Site Intelligence backend, review deployment health, and manage private/public dashboard placement.</p>
            <div class="scsi-admin-panel-grid">
                <div class="scsi-admin-panel"><h2>Connection</h2><p>Confirm the Render backend URL, API token, and current deployed version.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-status')); ?>" target="_blank" rel="noopener">Open Admin Status</a></p></div>
                <div class="scsi-admin-panel"><h2>Diagnostics</h2><p>Use the one-click diagnostic summary after each deploy.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-diagnostic-summary')); ?>" target="_blank" rel="noopener">Open Diagnostic Summary</a></p></div>
                <div class="scsi-admin-panel"><h2>Public / Private</h2><p>Keep raw analytics, reports, AI drafts, and admin diagnostics on private pages.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-public-readiness-check')); ?>" target="_blank" rel="noopener">Open Public Readiness</a></p></div>
            </div>
            <form method="post" action="options.php">
                <?php settings_fields('sc_site_intelligence'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="scsi_backend_url">Backend URL</label></th>
                        <td>
                            <input id="scsi_backend_url" type="url" class="regular-text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[backend_url]" value="<?php echo esc_attr($options['backend_url']); ?>" placeholder="https://your-render-service.onrender.com" />
                            <p class="description">Do not include a trailing slash.</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="scsi_api_token">API Token</label></th>
                        <td>
                            <input id="scsi_api_token" type="password" class="regular-text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[api_token]" value="<?php echo esc_attr($options['api_token']); ?>" autocomplete="off" />
                            <p class="description">Stored in WordPress and sent server-side to the backend. It is not exposed to browser JavaScript.</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Event Bridge</th>
                        <td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_KEY); ?>[enable_event_bridge]" value="1" <?php checked($options['enable_event_bridge'], '1'); ?> /> Emit Sustainable Catalyst custom events.</label></td>
                    </tr>
                    <tr>
                        <th scope="row">Shortcode Dashboard</th>
                        <td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_KEY); ?>[enable_dashboard]" value="1" <?php checked($options['enable_dashboard'], '1'); ?> /> Enable dashboard shortcodes.</label></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <hr />
            <h2>Shortcodes</h2>
            <p><code>[sc_site_intelligence_dashboard]</code></p>
            <p><code>[sc_site_intelligence_page]</code></p>
            <p><code>[sc_site_intelligence_unmapped]</code></p>
            <p><code>[sc_site_intelligence_events]</code></p>
            <p><code>[sc_site_intelligence_opportunities]</code></p>
            <p><code>[sc_external_data_health]</code></p>
            <p><code>[sc_climate_energy_intelligence]</code></p>
            <p><code>[sc_external_cache_status]</code></p>
            <p><code>[sc_search_intelligence]</code></p>
            <p><code>[sc_search_opportunities]</code></p>
            <p><code>[sc_metadata_intelligence]</code></p>
            <p><code>[sc_internal_link_intelligence]</code></p>
            <p><code>[sc_seo_recommendations]</code></p>
            <p><code>[sc_indexing_intelligence]</code></p>
            <p><code>[sc_sitemap_coverage]</code></p>
            <p><code>[sc_404_intelligence]</code></p>
            <p><code>[sc_advanced_external_data_health]</code></p>
            <p><code>[sc_environmental_monitoring_intelligence]</code></p>
            <p><code>[sc_urban_resilience_intelligence]</code></p>
            <p><code>[sc_biodiversity_land_use_intelligence]</code></p>
            <p><code>[sc_energy_systems_intelligence]</code></p>
            <h2>Public Source Pages</h2>
            <p><code>[sc_public_source_page_directory]</code></p>
            <p><code>[sc_public_source_navigation]</code></p>
            <p><code>[sc_public_source_page_templates]</code></p>
            <p><code>[sc_public_source_page_visual_qa]</code></p>
            <h2>Public Connector Status</h2>
            <p><code>[sc_public_connector_status]</code></p>
            <p><code>[sc_public_cache_status]</code></p>
            <p><code>[sc_public_source_freshness]</code></p>
            <p><code>[sc_public_world_bank_connector]</code></p>
            <p><code>[sc_public_openalex_connector]</code></p>
            <p><code>[sc_public_crossref_connector]</code></p>
            <p><code>[sc_public_github_connector]</code></p>
            <p><code>[sc_public_environmental_connectors]</code></p>
            <h2>AI-Assisted Briefs</h2>
            <p><code>[sc_ai_brief_status]</code></p>
            <p><code>[sc_ai_site_intelligence_brief]</code></p>
            <p><code>[sc_ai_search_brief]</code></p>
            <p><code>[sc_ai_publishing_brief]</code></p>
            <p><code>[sc_ai_external_sources_brief]</code></p>
            <p><code>[sc_ai_public_dashboard_brief]</code></p>
            <h2>Admin Control Plane</h2>
            <p><code>[sc_site_intelligence_admin_overview]</code></p>
            <p><code>[sc_site_intelligence_shortcode_catalog]</code></p>
            <p><code>[sc_site_intelligence_module_status]</code></p>
            <p><code>[sc_site_intelligence_diagnostic_summary]</code></p>
            <p><code>[sc_site_intelligence_connection_check]</code></p>
            <p><code>[sc_site_intelligence_release_status]</code></p>
            <h2>Diagnostics</h2>
            <p>After saving settings, open <a href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/diagnostics/ga4')); ?>" target="_blank" rel="noopener">GA4 diagnostics</a> while logged in.</p>
        </div>
        <?php
    }

    public function enqueue_assets() {
        $options = self::options();
        $base = plugin_dir_url(__FILE__) . 'assets/';
        wp_enqueue_style('sc-site-intelligence', $base . 'sc-site-intelligence.css', [], self::VERSION);
        wp_enqueue_script('sc-site-intelligence', $base . 'sc-site-intelligence.js', [], self::VERSION, true);
        wp_localize_script('sc-site-intelligence', 'SCSiteIntelligence', [
            'restBase' => esc_url_raw(rest_url(self::REST_NAMESPACE)),
            'restNonce' => wp_create_nonce('wp_rest'),
            'enableEventBridge' => $options['enable_event_bridge'] === '1',
            'pagePath' => wp_parse_url(home_url(add_query_arg([])), PHP_URL_PATH),
            'pageTitle' => wp_get_document_title(),
            'siteUrl' => home_url('/'),
            'version' => self::VERSION,
        ]);
    }

    public function dashboard_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-dashboard" data-scsi-dashboard>
            <p class="scsi-eyebrow">Sustainable Catalyst Intelligence</p>
            <h2>Site Intelligence Dashboard</h2>
            <p class="scsi-muted">Loading analytics interpretation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function page_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-page" data-scsi-page>
            <p class="scsi-eyebrow">Page Intelligence</p>
            <h2>This Page in the Knowledge System</h2>
            <p class="scsi-muted">Loading page-level analytics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function unmapped_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-unmapped" data-scsi-unmapped>
            <p class="scsi-eyebrow">Registry Intelligence</p>
            <h2>Unmapped and Inferred Pages</h2>
            <p class="scsi-muted">Loading registry mapping report…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function events_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-events" data-scsi-events>
            <p class="scsi-eyebrow">Conversion Validation</p>
            <h2>Event Tracking Diagnostics</h2>
            <p class="scsi-muted">Loading event diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-opportunities" data-scsi-opportunities>
            <p class="scsi-eyebrow">Conversion Opportunities</p>
            <h2>Page-Level CTA and Pathway Opportunities</h2>
            <p class="scsi-muted">Loading conversion opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function external_health_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-external-health" data-scsi-external-health>
            <p class="scsi-eyebrow">External Data Intelligence</p>
            <h2>External Data Connector Health</h2>
            <p class="scsi-muted">Loading external connector status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function climate_energy_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
        ], $atts, 'sc_climate_energy_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-climate-energy" data-scsi-climate-energy
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>"
            data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>"
            data-start="<?php echo esc_attr($atts['start']); ?>"
            data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>"
            data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow">Climate + Energy Intelligence</p>
            <h2>Climate + Energy Intelligence Pilot</h2>
            <p class="scsi-muted">Loading NASA POWER, NASA GIBS, and Climate TRACE connector data…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function external_cache_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-external-cache" data-scsi-external-cache>
            <p class="scsi-eyebrow">External Data Cache</p>
            <h2>External Source Cache Status</h2>
            <p class="scsi-muted">Loading source cache status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function search_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
        ], $atts, 'sc_search_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-search-intelligence" data-scsi-search-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Search Intelligence</p>
            <h2>Search Console and SEO Intelligence</h2>
            <p class="scsi-muted">Loading Search Console performance and Sustainable Catalyst SEO interpretation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function search_opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_search_opportunities');
        ob_start();
        ?>
        <section class="scsi-card scsi-search-opportunities" data-scsi-search-opportunities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">SEO Opportunities</p>
            <h2>Search Opportunity Pages</h2>
            <p class="scsi-muted">Loading high-impression, low-CTR, and near-position opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function metadata_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_metadata_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-metadata-intelligence" data-scsi-metadata-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Metadata Intelligence</p>
            <h2>Metadata, Titles, and CTR Review</h2>
            <p class="scsi-muted">Loading title, query alignment, and metadata review priorities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function internal_link_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_internal_link_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-internal-link-intelligence" data-scsi-internal-link-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Internal Link Intelligence</p>
            <h2>Internal Link and Pathway Opportunities</h2>
            <p class="scsi-muted">Loading internal-link priorities from Search Console and the registry…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function seo_recommendations_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_seo_recommendations');
        ob_start();
        ?>
        <section class="scsi-card scsi-seo-recommendations" data-scsi-seo-recommendations
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">SEO Recommendation Intelligence</p>
            <h2>Metadata and Internal-Link Action Queue</h2>
            <p class="scsi-muted">Loading combined metadata and internal-link recommendations…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function indexing_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
        ], $atts, 'sc_indexing_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-indexing-intelligence" data-scsi-indexing-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Indexing Intelligence</p>
            <h2>Sitemap, Indexing, and Registry Coverage</h2>
            <p class="scsi-muted">Loading sitemap, registry, GA4, and Search Console coverage…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function sitemap_coverage_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-sitemap-coverage" data-scsi-sitemap-coverage>
            <p class="scsi-eyebrow">Sitemap Coverage</p>
            <h2>XML Sitemap and Registry Alignment</h2>
            <p class="scsi-muted">Loading sitemap coverage…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function four_oh_four_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_404_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-404-intelligence" data-scsi-404-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">404 Intelligence</p>
            <h2>404 and Routing Diagnostics</h2>
            <p class="scsi-muted">Loading 404 and routing diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function publishing_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '20',
        ], $atts, $shortcode);
    }

    public function content_strategy_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_content_strategy_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-content-strategy" data-scsi-content-strategy
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Publishing Intelligence</p>
            <h2>Content Strategy and Publishing Intelligence</h2>
            <p class="scsi-muted">Loading publishing strategy signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function topic_momentum_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_topic_momentum');
        ob_start();
        ?>
        <section class="scsi-card scsi-topic-momentum" data-scsi-topic-momentum
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Topic Momentum</p>
            <h2>Article Map and Topic Momentum</h2>
            <p class="scsi-muted">Loading topic momentum and article-map performance…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function update_priorities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_update_priorities');
        ob_start();
        ?>
        <section class="scsi-card scsi-update-priorities" data-scsi-update-priorities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Update Priorities</p>
            <h2>Content Decay, Rising Pages, and Update Queue</h2>
            <p class="scsi-muted">Loading update priorities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function publishing_opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_publishing_opportunities');
        ob_start();
        ?>
        <section class="scsi-card scsi-publishing-opportunities" data-scsi-publishing-opportunities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Publishing Opportunities</p>
            <h2>Promotion, Newsletter, GitHub, and Tool Opportunities</h2>
            <p class="scsi-muted">Loading publishing promotion opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function public_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
            'live' => '',
        ], $atts, $shortcode);
    }



    public function public_flagship_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'title' => 'Sustainable Catalyst Site Intelligence',
            'subtitle' => 'A public-safe dashboard for knowledge architecture, public source signals, methodology, and platform transparency.',
            'show_cta' => 'true',
        ], $atts, 'sc_site_intelligence_public_flagship');
        ob_start();
        ?>
        <section class="scsi-public-flagship" data-scsi-public-flagship>
            <div class="scsi-flagship-hero">
                <p class="scsi-eyebrow">Sustainable Catalyst Site Intelligence</p>
                <h2><?php echo esc_html($atts['title']); ?></h2>
                <p class="scsi-flagship-lede"><?php echo esc_html($atts['subtitle']); ?></p>
                <p class="scsi-public-boundary">Educational and informational only. This page does not provide legal, financial, medical, engineering, climate-risk, ESG, compliance, assurance, or investment advice.</p>
                <?php if ($atts['show_cta'] !== 'false') : ?>
                <div class="scsi-public-cta-row scsi-flagship-cta-row">
                    <a class="scsi-public-cta" href="https://sustainablecatalyst.com/research-library/" data-scsi-event="sc_library_nav">Explore the Research Library</a>
                    <a class="scsi-public-cta" href="https://sustainablecatalyst.com/workbench/" data-scsi-event="sc_workbench_open">Open the Workbench</a>
                    <a class="scsi-public-cta" href="https://github.com/Content-Catalyst-LLC" target="_blank" rel="noopener" data-scsi-event="sc_repository_click">View the GitHub Repositories</a>
                </div>
                <?php endif; ?>
            </div>
            <div class="scsi-flagship-stack">
                <?php
                echo $this->public_landing_shortcode([]);
                echo $this->public_site_intelligence_shortcode([]);
                echo $this->public_knowledge_overview_shortcode([]);
                echo $this->public_climate_energy_summary_shortcode([]);
                echo $this->public_methodology_shortcode([]);
                ?>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_page_builder_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-page-builder" data-scsi-public-page-builder>
            <p class="scsi-eyebrow">Public Dashboard Page Builder</p>
            <h2>Public Flagship Dashboard Page Builder</h2>
            <p class="scsi-muted">Loading public-safe page presets, release checklist, and placement guidance…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_shortcode_bundle_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-shortcode-bundle" data-scsi-public-shortcode-bundle>
            <p class="scsi-eyebrow">Public Dashboard Shortcode Bundles</p>
            <h2>Copy-Ready Public Dashboard Bundles</h2>
            <p class="scsi-muted">Loading public-safe shortcode bundles…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_visual_qa_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-visual-qa" data-scsi-public-visual-qa>
            <p class="scsi-eyebrow">Public Dashboard Visual QA</p>
            <h2>Visual QA and Copy Polish</h2>
            <p class="scsi-muted">Loading public dashboard visual QA, copy guidance, and launch notes…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_landing_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-landing" data-scsi-public-landing>
            <p class="scsi-eyebrow">Sustainable Catalyst Site Intelligence</p>
            <h2>Public Dashboard Framework</h2>
            <p class="scsi-muted">Loading public Site Intelligence landing overview…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_site_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_site_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-dashboard" data-scsi-public-dashboard
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Public Site Intelligence</p>
            <h2>Sustainable Catalyst Public Intelligence Overview</h2>
            <p class="scsi-muted">Loading public-safe knowledge-system summary…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_knowledge_overview_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_knowledge_overview');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-knowledge-overview" data-scsi-public-knowledge-overview
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Knowledge-System Overview</p>
            <h2>Knowledge Areas and Public Surfaces</h2>
            <p class="scsi-muted">Loading public-safe knowledge-area overview…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_climate_energy_summary_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_climate_energy_summary');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-climate-energy" data-scsi-public-climate-energy
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>"
            data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>"
            data-start="<?php echo esc_attr($atts['start']); ?>"
            data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>"
            data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow">Climate + Energy Public Summary</p>
            <h2>Climate, Energy, and External Source Snapshot</h2>
            <p class="scsi-muted">Loading public-safe climate and energy summary…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_methodology_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-methodology" data-scsi-public-methodology>
            <p class="scsi-eyebrow">Public Dashboard Methodology</p>
            <h2>What Public Site Intelligence Shows and Hides</h2>
            <p class="scsi-muted">Loading public methodology and source notes…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }



    public function public_dashboard_navigation_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'current' => '',
            'title' => 'Site Intelligence Public Dashboards',
        ], $atts, 'sc_public_dashboard_navigation');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-dashboard-navigation" data-scsi-public-dashboard-navigation data-current="<?php echo esc_attr(sanitize_key($atts['current'])); ?>">
            <p class="scsi-eyebrow">Dashboard Navigation</p>
            <h2><?php echo esc_html($atts['title']); ?></h2>
            <p class="scsi-muted">Loading public dashboard navigation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_topic_page_templates_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'slug' => '',
            'title' => 'Public Topic Page Templates',
        ], $atts, 'sc_public_topic_page_templates');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-page-templates" data-scsi-public-topic-page-templates data-slug="<?php echo esc_attr(sanitize_key($atts['slug'])); ?>">
            <p class="scsi-eyebrow">Page Templates</p>
            <h2><?php echo esc_html($atts['title']); ?></h2>
            <p class="scsi-muted">Loading public topic page templates…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_topic_page_visual_qa_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-page-visual-qa" data-scsi-public-topic-page-visual-qa>
            <p class="scsi-eyebrow">Topic Page QA</p>
            <h2>Site Intelligence Public Topic Page QA</h2>
            <p class="scsi-muted">Loading public topic page QA…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_dashboard_directory_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-directory" data-scsi-public-dashboard-directory>
            <p class="scsi-eyebrow">Public Topic Dashboards</p>
            <h2>Public Dashboard Directory</h2>
            <p class="scsi-muted">Loading public-safe topic dashboard directory…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function topic_from_shortcode_tag($tag) {
        $map = [
            'sc_public_climate_energy_dashboard' => 'climate-energy',
            'sc_public_environmental_monitoring_dashboard' => 'environmental-monitoring',
            'sc_public_biodiversity_land_use_dashboard' => 'biodiversity-land-use',
            'sc_public_knowledge_system_dashboard' => 'knowledge-system',
            'sc_public_search_discovery_dashboard' => 'search-discovery',
        ];
        return isset($map[$tag]) ? $map[$tag] : 'knowledge-system';
    }

    public function public_topic_dashboard_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $topic = $this->topic_from_shortcode_tag($tag);
        $titles = [
            'climate-energy' => 'Climate + Energy Public Dashboard',
            'environmental-monitoring' => 'Environmental Monitoring Public Dashboard',
            'biodiversity-land-use' => 'Biodiversity + Land Use Public Dashboard',
            'knowledge-system' => 'Knowledge-System Public Dashboard',
            'search-discovery' => 'Search + Discovery Public Dashboard',
        ];
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-dashboard" data-scsi-public-topic-dashboard data-topic="<?php echo esc_attr($topic); ?>">
            <p class="scsi-eyebrow">Public Topic Dashboard</p>
            <h2><?php echo esc_html($titles[$topic]); ?></h2>
            <p class="scsi-muted">Loading public-safe topic dashboard…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_source_methodology_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-source-methodology" data-scsi-public-source-methodology>
            <p class="scsi-eyebrow">Public Source Methodology</p>
            <h2>Source Notes, Fallbacks, and Public Boundaries</h2>
            <p class="scsi-muted">Loading public source methodology…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_api_sources_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-api-sources" data-scsi-public-source-panel data-source-panel="api-sources">
            <p class="scsi-eyebrow">Public API Sources</p>
            <h2>Public API Source Expansion</h2>
            <p class="scsi-muted">Loading public API source families…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function public_source_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_source_health' => ['source-health', 'Public Source Health', 'Source-health labels for live, cached, fallback, and planned source families.'],
            'sc_public_development_indicators' => ['development-indicators', 'Development Indicators', 'World Bank, OECD, and UN/SDG indicator context for public dashboards.'],
            'sc_public_research_metadata' => ['research-metadata', 'Research Metadata', 'OpenAlex and Crossref research metadata context for public source discovery.'],
            'sc_public_publication_metadata' => ['publication-metadata', 'Publication Metadata', 'Publication and DOI metadata context for public bibliography/source panels.'],
            'sc_public_repository_intelligence' => ['repository-intelligence', 'Repository Intelligence', 'GitHub repository intelligence for public code-infrastructure visibility.'],
            'sc_public_indicator_overview' => ['indicator-overview', 'Indicator Overview', 'Public indicator overview across live, cached, fallback, and planned source families.'],
            'sc_public_sustainability_indicators' => ['sustainability-indicators', 'Sustainability Indicators', 'Sustainability indicator context across environment, development, research, and repository layers.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['source-health', 'Public Source Health', 'Loading public source panel…'];
    }

    public function public_source_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_source_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-source-panel" data-scsi-public-source-panel data-source-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Source Layer</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function public_connector_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_connector_status' => ['connector-status', 'Public Connector Status', 'Live, cached, fallback, and planned connector readiness for public source panels.'],
            'sc_public_cache_status' => ['cache-status', 'Public Cache Status', 'Cache TTL, stale-safe display, and public source refresh policy.'],
            'sc_public_source_freshness' => ['source-freshness', 'Public Source Freshness', 'Freshness labels for public source families and connector panels.'],
            'sc_public_world_bank_connector' => ['world-bank', 'World Bank Connector', 'Development indicator source status, cache policy, and fallback notes.'],
            'sc_public_openalex_connector' => ['openalex', 'OpenAlex Connector', 'Research metadata source status, cache policy, and fallback notes.'],
            'sc_public_crossref_connector' => ['crossref', 'Crossref Connector', 'Publication metadata source status, cache policy, and fallback notes.'],
            'sc_public_github_connector' => ['github', 'GitHub Connector', 'Repository intelligence source status, cache policy, and fallback notes.'],
            'sc_public_environmental_connectors' => ['environmental', 'Environmental Connectors', 'NASA, NOAA, EPA, EIA, USGS, GBIF, and Climate TRACE public source status.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['connector-status', 'Public Connector Status', 'Loading public connector status…'];
    }

    public function public_connector_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_connector_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Connector Layer</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_dashboard_readiness_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_dashboard_readiness');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-readiness" data-scsi-public-readiness
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Public Dashboard Readiness</p>
            <h2>Internal Public-Release Checklist</h2>
            <p class="scsi-muted">Loading public-readiness diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function advanced_external_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'state' => '',
            'county' => '',
            'start' => '',
            'end' => '',
            'force_refresh' => '',
        ], $atts, $shortcode);
    }

    public function advanced_external_health_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-advanced-external-health" data-scsi-advanced-external-health>
            <p class="scsi-eyebrow">Advanced External Data</p>
            <h2>Advanced External Connector Health</h2>
            <p class="scsi-muted">Loading NOAA, EIA, EPA, Census, USGS, and GBIF connector health…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function environmental_monitoring_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_environmental_monitoring_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-environmental-monitoring" data-scsi-environmental-monitoring
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-county="<?php echo esc_attr($atts['county']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Environmental Monitoring</p>
            <h2>Environmental Monitoring Intelligence</h2>
            <p class="scsi-muted">Loading environmental monitoring signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function urban_resilience_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_urban_resilience_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-urban-resilience" data-scsi-urban-resilience
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-county="<?php echo esc_attr($atts['county']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Urban Resilience</p>
            <h2>Urban Resilience Intelligence</h2>
            <p class="scsi-muted">Loading urban resilience signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function biodiversity_land_use_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_biodiversity_land_use_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-biodiversity-land-use" data-scsi-biodiversity-land-use
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Biodiversity + Land Use</p>
            <h2>Biodiversity and Land Use Intelligence</h2>
            <p class="scsi-muted">Loading biodiversity and land-use signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function energy_systems_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_energy_systems_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-energy-systems" data-scsi-energy-systems
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-start="<?php echo esc_attr($atts['start']); ?>" data-end="<?php echo esc_attr($atts['end']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Energy Systems</p>
            <h2>Energy Systems Data Intelligence</h2>
            <p class="scsi-muted">Loading energy systems signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }


    private function report_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '',
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
            'live' => '',
            'report' => '',
        ], $atts, $shortcode);
    }

    private function report_shortcode($atts, $shortcode, $type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->report_shortcode_atts($atts, $shortcode);
        ob_start(); ?>
        <section class="scsi-card scsi-report-card" data-scsi-report data-report-type="<?php echo esc_attr($type); ?>"
            data-start-date="<?php echo esc_attr($atts['start_date']); ?>" data-end-date="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start-date="<?php echo esc_attr($atts['prior_start_date']); ?>" data-prior-end-date="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>" data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>" data-start="<?php echo esc_attr($atts['start']); ?>" data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>" data-live="<?php echo esc_attr($atts['live']); ?>" data-report="<?php echo esc_attr($atts['report']); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function site_intelligence_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_site_intelligence_report', 'site-intelligence', 'Report Generator', 'Weekly Site Intelligence Report', 'Loading Site Intelligence report…');
    }

    public function search_intelligence_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_search_intelligence_report', 'search-intelligence', 'Search Report', 'Search Intelligence Report', 'Loading Search Intelligence report…');
    }

    public function content_strategy_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_content_strategy_report', 'content-strategy', 'Publishing Report', 'Content Strategy Report', 'Loading Content Strategy report…');
    }

    public function external_sources_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_external_sources_report', 'external-sources', 'External Sources Report', 'External Data Source Brief', 'Loading External Sources report…');
    }

    public function climate_energy_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_climate_energy_report', 'climate-energy', 'Climate + Energy Report', 'Climate + Energy Snapshot Report', 'Loading Climate + Energy report…');
    }

    public function indexing_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_indexing_report', 'indexing', 'Indexing Report', 'Registry and Indexing Coverage Report', 'Loading Indexing Coverage report…');
    }

    public function report_export_bundle_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_report_export_bundle', 'export', 'Export Bundle', 'Site Intelligence Export Bundle', 'Loading export bundle summary…');
    }


    private function ai_brief_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '',
            'mode' => '',
            'use_ai' => '',
            'live' => '',
        ], $atts, $shortcode);
    }

    public function ai_brief_status_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-ai-status" data-scsi-ai-status>
            <p class="scsi-eyebrow">AI Briefs</p>
            <h2>AI Brief Provider Status</h2>
            <p class="scsi-muted">Loading AI provider status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    private function ai_brief_shortcode($atts, $shortcode, $type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->ai_brief_shortcode_atts($atts, $shortcode);
        ob_start(); ?>
        <section class="scsi-card scsi-ai-brief-card" data-scsi-ai-brief data-brief-type="<?php echo esc_attr($type); ?>"
            data-start-date="<?php echo esc_attr($atts['start_date']); ?>" data-end-date="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start-date="<?php echo esc_attr($atts['prior_start_date']); ?>" data-prior-end-date="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>" data-mode="<?php echo esc_attr($atts['mode']); ?>" data-use-ai="<?php echo esc_attr($atts['use_ai']); ?>" data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function ai_site_intelligence_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_site_intelligence_brief', 'site-intelligence', 'AI-Assisted Brief', 'Weekly Site Intelligence Brief', 'Loading AI-assisted Site Intelligence brief…');
    }

    public function ai_search_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_search_brief', 'search', 'AI-Assisted Brief', 'Search Intelligence Brief', 'Loading AI-assisted Search brief…');
    }

    public function ai_publishing_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_publishing_brief', 'publishing', 'AI-Assisted Brief', 'Publishing Strategy Brief', 'Loading AI-assisted Publishing brief…');
    }

    public function ai_external_sources_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_external_sources_brief', 'external-sources', 'AI-Assisted Brief', 'External Data Sources Brief', 'Loading AI-assisted External Sources brief…');
    }

    public function ai_public_dashboard_brief_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = shortcode_atts([
            'live' => '',
        ], $atts, 'sc_ai_public_dashboard_brief');
        if ($atts['live'] === 'true' || $atts['live'] === '1') {
            return $this->ai_brief_shortcode($atts, 'sc_ai_public_dashboard_brief', 'public-dashboard', 'AI-Assisted Brief', 'Public Dashboard Brief', 'Loading AI-assisted Public Dashboard brief…');
        }
        $brief = $this->local_public_dashboard_ai_brief();
        ob_start(); ?>
        <section class="scsi-card scsi-ai-brief-card scsi-ai-public-dashboard-local">
            <p class="scsi-eyebrow">AI-Assisted Brief</p>
            <h2>Public Dashboard Brief</h2>
            <p class="scsi-muted">Provider: <?php echo esc_html($brief['provider']); ?> · Model: <?php echo esc_html($brief['model']); ?> · Mode: public · Source: local public-safe fallback</p>
            <div class="scsi-output" aria-live="polite">
                <div class="scsi-ai-summary"><h3>Executive summary</h3><p><?php echo esc_html($brief['executive_summary']); ?></p></div>
                <p class="scsi-muted scsi-ai-confidence">Confidence: <?php echo esc_html($brief['confidence']['level']); ?> · <?php echo esc_html($brief['confidence']['basis']); ?></p>
                <h3>Key findings</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['key_findings'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <h3>Recommended next actions</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['recommended_actions'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <h3>Risk and uncertainty notes</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['risk_notes'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <div class="scsi-ai-public-summary"><h3>Public-safe summary draft</h3><p><?php echo esc_html($brief['public_safe_summary']); ?></p></div>
            </div>
        </section>
        <?php return ob_get_clean();
    }


    private function admin_control_shortcode($type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        if (!current_user_can('manage_options')) {
            return '<section class="scsi-card scsi-admin-control-card"><p class="scsi-muted">Site Intelligence admin controls are private.</p></section>';
        }
        ob_start(); ?>
        <section class="scsi-card scsi-admin-control-card" data-scsi-admin-control data-admin-type="<?php echo esc_attr($type); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function admin_overview_shortcode($atts = []) {
        return $this->admin_control_shortcode('overview', 'Admin Control Plane', 'Site Intelligence Admin Overview', 'Loading registry, source, module, and diagnostic status…');
    }

    public function shortcode_catalog_shortcode($atts = []) {
        return $this->admin_control_shortcode('shortcodes', 'Admin Control Plane', 'Shortcode Catalog', 'Loading shortcode catalog and placement guidance…');
    }

    public function module_status_shortcode($atts = []) {
        return $this->admin_control_shortcode('modules', 'Admin Control Plane', 'Module Status Matrix', 'Loading module status and visibility matrix…');
    }

    public function diagnostic_summary_shortcode($atts = []) {
        return $this->admin_control_shortcode('diagnostic-summary', 'Admin Diagnostics', 'One-Click Diagnostic Summary', 'Loading backend, registry, source, module, shortcode, and visibility diagnostics…');
    }

    public function connection_check_shortcode($atts = []) {
        return $this->admin_control_shortcode('connection-check', 'Admin Diagnostics', 'Connection Check', 'Loading backend, token, registry, source, and public-readiness checks…');
    }

    public function release_status_shortcode($atts = []) {
        return $this->admin_control_shortcode('release-status', 'Public Flagship Release', 'Site Intelligence v1.3.0 Release Status', 'Loading release checklist, smoke-test guidance, public page metadata, and launch notes…');
    }

}

new SC_Site_Intelligence_Plugin();
