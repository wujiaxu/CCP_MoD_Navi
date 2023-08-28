using System.Collections;
using System.Collections.Generic;
using System.IO;
//using CodeMonkey.Utils;
using UnityEngine;
// using CodeMonkey.Utils;

public class ModManager : MonoBehaviour
{
    public Grid grid;
    [Tooltip("MoD Save directory")]
    public string MOD_file;
    int height;
    int width;
    // Start is called before the first frame update
    void Start()
    {
        StreamReader sr = new StreamReader(this.MOD_file);

        // string map_name = sr.ReadLine();
        this.height = 36; //int.Parse(sr.ReadLine());
        this.width = 60; // int.Parse(sr.ReadLine());
        grid = new Grid(this.width, this.height, 1f, new Vector3(-50f, 0, -12f));

        string currentLine;
        int h;
        int w;
        float weight;
        float m1;
        float m2;
        float cov00;
        float cov01;
        float cov10;
        float cov11;
        while ((currentLine = sr.ReadLine()) != null)
        {
            //Debug.Log(currentLine);
            var line = currentLine?.Split(',');
            h = (int)float.Parse(line[0]);
            w = (int)float.Parse(line[1]);
            weight = float.Parse(line[2]);
            // speed
            m1 = float.Parse(line[3]);
            // direction
            m2 = float.Parse(line[4]); 
            // add 0.1 to make sure cov is semi-positive definite
            cov00 = float.Parse(line[5]) + 0.1f;
            cov01 = float.Parse(line[6]);
            cov10 = float.Parse(line[7]); 
            cov11 = float.Parse(line[8]) + 0.1f;
            grid.SetValue(w,h,weight,new double[] { m1, m2 },new double[,] { { cov00, cov01 }, { cov10, cov11 } });
        }

    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            // grid.SetValue(UtilsClass.GetMouseWorldPosition(),1);
            // grid.SetValue(1, 1, 45);
            for (int i = 0; i < this.height; i++)
            {
           
                for (int j = 0; j < this.width; j++)
                {
                    grid.VizDirection(j, i);
                }

            }

        }

        if (Input.GetMouseButtonDown(1))
        {
            // Debug.Log(grid.GetValue(UtilsClass.GetMouseWorldPosition()));
            // grid.SetValue(1, 1, 135);
            grid.VizDirection(1, 1);
            
        }

    }
}
