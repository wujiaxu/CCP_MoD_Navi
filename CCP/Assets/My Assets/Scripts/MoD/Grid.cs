using System.Collections;
using System.Collections.Generic;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.UIElements;
using Accord.MachineLearning;
using Accord.Statistics.Distributions.Univariate;
using Accord.Statistics.Distributions.Multivariate;

// using CodeMonkey.Utils;


public class Cell
{
    public Cell()
    {
        this.weights = new List<double>();
        this.gausses = new List<MultivariateNormalDistribution>();
    }
    public void AddGaussianDistribution(double[] mean, double[,] cov, double weight)
    {
        this.weights.Add(weight);
        this.gausses.Add(new MultivariateNormalDistribution(mean, cov));
    }
    public double GetProb(double[] V)
    {
        double prob = 0;
        for (int i = 0; i < this.weights.Count; i++)
        {
            prob += this.weights[i] * this.gausses[i].ProbabilityDensityFunction(V);
        }
        return prob;
    }

    public void GetDirections(List<double> direction)
    {
        foreach(MultivariateNormalDistribution gauss in this.gausses)
        {
            direction.Add(gauss.Mean[1]);
        }
    }
    private List<double> weights;
    private List<MultivariateNormalDistribution> gausses;
}

public class Grid
{
    private int width;
    private int height;
    private float cellSize;
    Vector3 originPosition;
    private Cell[,] gridArray;
    // private TextMesh[,] debugTextArray;

    public Grid(int width, int height, float cellSize, Vector3 originPosition)
    {
        this.width = width;
        this.height = height;
        this.originPosition = originPosition;
        this.cellSize = cellSize;
        gridArray = new Cell[width,height];
        // debugTextArray = new TextMesh[width, height];
        for (int x = 0; x < gridArray.GetLength(0); x++)
        {
            for(int y = 0; y < gridArray.GetLength(1); y++)
            {
                //debugTextArray[x, y] = UtilsClass.CreateWorldText(gridArray[x, y].ToString(), null, GetWorldPosition(x, y) + new Vector3(cellSize, cellSize) * .5f, 20, Color.white, TextAnchor.MiddleCenter);
                Debug.DrawLine(GetWorldPosition(x, y), GetWorldPosition(x, y + 1), Color.white, 100f);
                Debug.DrawLine(GetWorldPosition(x, y), GetWorldPosition(x + 1, y), Color.white, 100f);
                this.gridArray[x,y] = new Cell();
            }
        }
        Debug.DrawLine(GetWorldPosition(0, height), GetWorldPosition(width, height), Color.white, 100f);
        Debug.DrawLine(GetWorldPosition(width, 0), GetWorldPosition(width, height), Color.white, 100f);
    }
    Vector3 GetWorldPosition(int x, int z)
    {
        return new Vector3(x, 0f, z) * cellSize + originPosition;
    }

    void GetXY(Vector3 worldPosition, out int x, out int y)
    {
        x = Mathf.FloorToInt((worldPosition - originPosition).x / cellSize);
        y = Mathf.FloorToInt((worldPosition - originPosition).z / cellSize);
    }

    public void SetValue(int x, int y, double weight, double[] mean, double[,] cov)
    {
        if (x >= 0 && y >= 0 && x < width && y < height)
        {
            this.gridArray[x, y].AddGaussianDistribution(mean, cov, weight);
            //debugTextArray[x, y].text = gridArray[x, y].ToString();
            //Debug.Log(this.gridArray[x, y].weights.Count);
        }

    }

    public void SetValue(Vector3 worldPosition, double weight, double[] mean, double[,] cov)
    {
        int x, y;
        GetXY(worldPosition, out x, out y);
        SetValue(x, y, weight,mean,cov);

    }

    public int GetDirections(int x, int y, List<double> directions)
    {
        if (x >= 0 && y >= 0 && x < width && y < height)
        {
            this.gridArray[x, y].GetDirections(directions);
            return 0;
        }
        else
        {
            return -1;
        }
    }
    public int GetDirections(Vector3 worldPosition, List<double> directions)
    {
        int x, y;
        GetXY(worldPosition, out x, out y);
        return GetDirections(x, y, directions);

    }

    public double GetProb(int x, int y, double[] V)
    {
        if (x >= 0 && y >= 0 && x < width && y < height)
        {
            return this.gridArray[x, y].GetProb(V);
        }
        else
        {
            return -1;
        }
    }
    public double GetProb(Vector3 worldPosition, double[] V)
    {
        int x, y;
        GetXY(worldPosition, out x, out y);
        return GetProb(x, y, V);

    }


    public void VizDirection(Vector3 worldPosition)
    {
        int x, y;
        
        GetXY(worldPosition, out x, out y);
        VizDirection(x,y);


    }

    public void VizDirection(int x, int y)
    {
        List<double> angle_radians = new List<double>();
        if(GetDirections(x, y, angle_radians) < 0)
        {
            return;
        }
        foreach(float angle_radian in angle_radians)
        {
            //debug.drawline(getworldposition(x, y), getworldposition(x + 1, y), color.white, 100f);
            Debug.DrawRay(GetWorldPosition(x, y) + new Vector3(cellSize / 2f, 0f, cellSize / 2f), new Vector3(Mathf.Cos(angle_radian), 0f, Mathf.Sin(angle_radian)), Color.yellow, 80f);
        }
    }
}
