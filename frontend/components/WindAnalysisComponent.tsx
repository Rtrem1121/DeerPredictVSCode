import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Minus, TrendingDown, TrendingUp, Wind } from 'lucide-react';
import React from 'react';

// Types for wind analysis data
interface WindAnalysisData {
    current_wind_conditions: {
        prevailing_wind: string;
        thermal_activity: boolean;
        wind_conditions_summary: string;
    };
    location_wind_analyses: Array<{
        location_type: string;
        coordinates?: [number, number];
        wind_analysis: {
            effective_wind_direction: number;
            effective_wind_speed: number;
            wind_advantage_rating: number;
            prevailing_wind_direction?: number;
            thermal_wind_direction?: number;
            combined_wind_vector?: number;
        };
    }>;
    overall_wind_conditions: {
        hunting_rating: string;
        conditions_summary?: string;
        thermal_status?: string;
    };
}

interface WindAnalysisComponentProps {
    windAnalysis: WindAnalysisData | null;
    isLoading?: boolean;
}

const WindAnalysisComponent: React.FC<WindAnalysisComponentProps> = ({
    windAnalysis,
    isLoading = false
}) => {
    if (isLoading) {
        return (
            <Card className="w-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Wind className="h-5 w-5" />
                        Wind Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="animate-pulse space-y-4">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-8 bg-gray-200 rounded"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!windAnalysis) {
        return (
            <Card className="w-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Wind className="h-5 w-5" />
                        Wind Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-500">No wind analysis data available</p>
                </CardContent>
            </Card>
        );
    }

    const getRatingColor = (rating: number): string => {
        if (rating >= 8) return 'bg-green-100 text-green-800 border-green-200';
        if (rating >= 6) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-red-100 text-red-800 border-red-200';
    };

    const getRatingIcon = (rating: number) => {
        if (rating >= 8) return <TrendingUp className="h-4 w-4" />;
        if (rating >= 6) return <Minus className="h-4 w-4" />;
        return <TrendingDown className="h-4 w-4" />;
    };

    const formatWindDirection = (degrees: number): string => {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    };

    const getLocationIcon = (locationType: string) => {
        switch (locationType.toLowerCase()) {
            case 'bedding':
                return '🛏️';
            case 'stand':
                return '🌲';
            case 'feeding':
                return '🌾';
            default:
                return '📍';
        }
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Wind className="h-5 w-5" />
                    Wind Analysis
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Current Wind Conditions */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-sm text-gray-700">Current Conditions</h4>
                    <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                        <div className="flex items-center justify-between">
                            <span className="font-medium">{windAnalysis.current_wind_conditions.prevailing_wind}</span>
                            {windAnalysis.current_wind_conditions.thermal_activity && (
                                <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                                    Thermal Active
                                </Badge>
                            )}
                        </div>
                        {windAnalysis.current_wind_conditions.wind_conditions_summary && (
                            <p className="text-sm text-gray-600 mt-2">
                                {windAnalysis.current_wind_conditions.wind_conditions_summary}
                            </p>
                        )}
                    </div>
                </div>

                {/* Overall Rating */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-sm text-gray-700">Overall Wind Rating</h4>
                    <div className="flex items-center gap-3">
                        <Badge
                            className={`${getRatingColor(parseFloat(windAnalysis.overall_wind_conditions.hunting_rating))} border px-3 py-2`}
                        >
                            <span className="flex items-center gap-2">
                                {getRatingIcon(parseFloat(windAnalysis.overall_wind_conditions.hunting_rating))}
                                {windAnalysis.overall_wind_conditions.hunting_rating}
                            </span>
                        </Badge>
                        {windAnalysis.overall_wind_conditions.conditions_summary && (
                            <span className="text-sm text-gray-600">
                                {windAnalysis.overall_wind_conditions.conditions_summary}
                            </span>
                        )}
                    </div>
                </div>

                {/* Location-Specific Analysis */}
                {windAnalysis.location_wind_analyses && windAnalysis.location_wind_analyses.length > 0 && (
                    <div className="space-y-3">
                        <h4 className="font-semibold text-sm text-gray-700">Location Analysis</h4>
                        <div className="space-y-3">
                            {windAnalysis.location_wind_analyses.map((location, index) => (
                                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{getLocationIcon(location.location_type)}</span>
                                            <span className="font-medium capitalize">{location.location_type}</span>
                                        </div>
                                        <Badge
                                            className={`${getRatingColor(location.wind_analysis.wind_advantage_rating)} border`}
                                        >
                                            {location.wind_analysis.wind_advantage_rating.toFixed(1)}/10
                                        </Badge>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-600">Wind Direction:</span>
                                            <div className="font-medium">
                                                {formatWindDirection(location.wind_analysis.effective_wind_direction)}
                                                ({location.wind_analysis.effective_wind_direction}°)
                                            </div>
                                        </div>
                                        <div>
                                            <span className="text-gray-600">Wind Speed:</span>
                                            <div className="font-medium">
                                                {location.wind_analysis.effective_wind_speed.toFixed(1)} mph
                                            </div>
                                        </div>
                                    </div>

                                    {/* Additional wind component details if available */}
                                    {(location.wind_analysis.prevailing_wind_direction || location.wind_analysis.thermal_wind_direction) && (
                                        <div className="mt-3 pt-3 border-t border-gray-200">
                                            <div className="text-xs text-gray-500 space-y-1">
                                                {location.wind_analysis.prevailing_wind_direction && (
                                                    <div>Prevailing: {formatWindDirection(location.wind_analysis.prevailing_wind_direction)}°</div>
                                                )}
                                                {location.wind_analysis.thermal_wind_direction && (
                                                    <div>Thermal: {formatWindDirection(location.wind_analysis.thermal_wind_direction)}°</div>
                                                )}
                                                {location.wind_analysis.combined_wind_vector && (
                                                    <div>Combined: {formatWindDirection(location.wind_analysis.combined_wind_vector)}°</div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Thermal Status Alert */}
                {windAnalysis.overall_wind_conditions.thermal_status && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-orange-600" />
                            <span className="text-sm font-medium text-orange-800">Thermal Conditions</span>
                        </div>
                        <p className="text-sm text-orange-700 mt-1">
                            {windAnalysis.overall_wind_conditions.thermal_status}
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default WindAnalysisComponent;
